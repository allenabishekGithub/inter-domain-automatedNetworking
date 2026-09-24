# Installing the data plane on a fresh Ubuntu VM

Everything needed to take a clean Ubuntu 24.04 LTS machine to a running
`client-a` → `server-b` service. Each step says what it installs, why the data
plane needs it, and how to prove it worked before moving on.

**Environment scope:** these instructions prepare a deployment and validation
host. A machine used only for design work does not need this emulation stack.
See the [build phases](paper-1-federated-evidence/plan.md#8-build-phases) for what runs where; Phase 0
onward needs a host prepared as below.

Three upstream projects need small local edits to build on Ubuntu 24.04. Those
edits, and the reason each one is necessary, are in
[Required upstream edits](#required-upstream-edits). They are not optional.

**Verified on:** Ubuntu 24.04.4 LTS, kernel 6.8/7.0 (AWS), Python 3.12.3,
Docker 29.7.2, Containerlab 0.77.0, Open vSwitch 3.3.4, Mininet 2.3.0
(`d7f399d`), Mininet-Optical `7ba048f`. Other combinations may work; these are
the ones the instructions below were exercised against.

## Contents

- [What gets installed and why](#what-gets-installed-and-why)
- [0. Base system](#0-base-system)
- [1. Docker](#1-docker)
- [2. Containerlab and the node images](#2-containerlab-and-the-node-images)
- [3. Mininet](#3-mininet)
- [4. Open vSwitch](#4-open-vswitch)
- [5. Mininet-Optical](#5-mininet-optical)
- [6. This repository](#6-this-repository)
- [7. Verify the whole stack](#7-verify-the-whole-stack)
- [Required upstream edits](#required-upstream-edits)
- [Which interpreter runs what](#which-interpreter-runs-what)
- [Troubleshooting](#troubleshooting)
- [Uninstalling](#uninstalling)

## What gets installed and why

| Component | Used by | Why it is needed |
|---|---|---|
| Docker | `packet-network` | Runs the eight SR Linux routers and four Linux nodes. |
| Containerlab | `packet-network` | Builds the topology, wires the veth links, manages node lifecycle. |
| SR Linux + Alpine images | `packet-network` | The router and endpoint/bridge images the topology names. |
| Mininet | `optical-network` | Supplies the namespaces, hosts and link plumbing the optical line is built from. |
| Open vSwitch | `optical-network` | Backs the emulated switches. Installed by Mininet's script, but see [step 4](#4-open-vswitch). |
| Mininet-Optical (`mnoptical`) | `optical-network` | The optical model: terminals, ROADMs, spans, amplifiers, monitors, and the control API. |
| Python 3.12 + venv | both | Client tooling (`pygnmi`, `requests`) and the test suites. |

### Sizing

The eight SR Linux containers dominate. The image alone is 3.19 GB, and each
running node wants roughly 1–2 GB of RAM. A practical floor is **4 vCPU, 16 GB
RAM and 40 GB of free disk**; below that the routers boot slowly or get killed.
This is guidance from the image size and node count rather than a measured
minimum — the reference machine was considerably larger and was never a
constraint.

Everything below assumes a user with `sudo`. The examples use `ubuntu`.

## 0. Base system

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    git curl ca-certificates build-essential \
    python3 python3-pip python3-venv \
    iproute2 net-tools
```

Check:

```bash
python3 --version     # expect 3.12.x
lsb_release -d        # expect Ubuntu 24.04
```

Ubuntu 24.04 ships Python 3.12 as an **externally managed** interpreter: there
is a marker file at `/usr/lib/python3.12/EXTERNALLY-MANAGED`, and `pip install`
into system Python is refused by default ([PEP 668](https://peps.python.org/pep-0668/)).
That single fact is behind two of the three upstream edits below, so it is
worth confirming now:

```bash
ls /usr/lib/python3.12/EXTERNALLY-MANAGED   # present on 24.04
```

## 1. Docker

Install from Docker's own repository rather than the `docker.io` archive
package — the archive version lags and has given Containerlab trouble. Remove
any conflicting packages first:

```bash
for pkg in docker.io docker-doc docker-compose docker-compose-v2 \
           podman-docker containerd runc; do
    sudo apt-get remove -y $pkg 2>/dev/null || true
done
```

Add the repository:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
     -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
                    docker-buildx-plugin docker-compose-plugin
```

Let your user drive Docker without `sudo`:

```bash
sudo usermod -aG docker $USER
newgrp docker          # or log out and back in
```

Check:

```bash
docker --version
docker run --rm hello-world
```

`docker run` must work **without** `sudo` before continuing. The bring-up
script, the traffic tooling and the optical attachment all call `docker exec`.

> Membership of the `docker` group is equivalent to root on this host. That is
> expected for a lab, and it is also why the data plane's per-domain scoping is
> documented as a correctness guard rather than isolation — see
> [the data-plane specification](data-plane.md#control-boundary).

## 2. Containerlab and the node images

```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```

The installer also creates a `clab_admins` group; adding yourself to it lets
some operations run without `sudo`, but the commands in this repository use
`sudo` explicitly and do not depend on it.

Check:

```bash
containerlab version
```

Pull the two images the topology names. Doing it now means the first deploy
does not silently spend several minutes pulling 3 GB:

```bash
docker pull ghcr.io/nokia/srlinux:24.10.1
docker pull alpine:3.20
docker images | grep -E 'srlinux|alpine'
```

Both tags are pinned in `packet-network/topology.clab.yml`. Change them there,
not here, and record the change in your experiment manifest.

## 3. Mininet

Mininet is installed **from source**, pinned to 2.3.0. Clone it outside this
repository — `$HOME` is fine:

```bash
cd ~
git clone https://github.com/mininet/mininet
cd mininet
git checkout -b mininet-2.3.0 2.3.0
```

### Apply the two required edits

Do this **before** running the installer. Both are explained in
[Required upstream edits](#required-upstream-edits).

```bash
# 1. Let `make install` write into the externally managed system interpreter.
sed -i 's|^\t\$(PYTHON) -m pip install \.$|\t$(PYTHON) -m pip install --break-system-packages .|' \
    Makefile

# 2. Drop the obsolete `pep8` apt package, which no longer exists in 24.04.
sed -i 's|^\(\s*\)ethtool help2man \$pf pylint pep8 \\$|\1ethtool help2man $pf pylint \\|' \
    util/install.sh
```

Confirm you changed exactly two lines and nothing else:

```bash
git diff --stat      # expect: Makefile | 2 +-   util/install.sh | 2 +-
git diff             # read it; it should match the diffs in this document
```

### Run the installer

```bash
cd ~
./mininet/util/install.sh -nv
```

`-n` installs Mininet's dependencies and core files; `-v` installs Open
vSwitch. **The two run in that order, and `-v` is skipped if `-n` fails** —
which is exactly what the `pep8` edit prevents. Do not assume Open vSwitch
arrived just because the script printed a lot of output; step 4 checks it
separately for this reason.

Check:

```bash
cd /tmp
mn --version                                        # expect 2.3.0
python3 -c "import mininet, os; print(os.path.dirname(mininet.__file__))"
sudo python3 -c "import mininet; print('privileged import ok')"
```

The last one matters most: the optical line runs as root, so **`sudo python3`**
is the interpreter that has to find `mininet`. Run these from `/tmp` or another
neutral directory — inside `~/mininet`, Python picks the source tree out of the
working directory and the check proves nothing.

Expect `/usr/local/lib/python3.12/dist-packages/mininet`.

## 4. Open vSwitch

Mininet's `-v` flag should have installed it. Verify separately, because a
failure earlier in the script leaves the system looking half-installed:

```bash
ovs-vsctl --version
systemctl is-active openvswitch-switch      # expect: active
systemctl is-enabled openvswitch-switch     # expect: enabled
```

If it is missing:

```bash
sudo apt install -y openvswitch-switch
sudo systemctl enable --now openvswitch-switch
```

Check the kernel module is loaded when a network is running:

```bash
lsmod | grep -E '^(openvswitch|veth|bridge) '
```

## 5. Mininet-Optical

```bash
cd ~
git clone https://github.com/mininet-optical/mininet-optical
cd mininet-optical
git checkout 7ba048f          # the revision these instructions were verified against
```

Omit the `checkout` to track `master`, but then record the revision you used —
the optical model's behaviour is part of your results.

### Apply the required edit

```bash
sed -i -E \
  's|^(\t+(sudo )?\$\(PIP\) install )(--upgrade --verbose dist/\*\.whl)$|\1--break-system-packages \3|; '\
's|^(\tsudo \$\(PIP\) install )(-r requirements\.txt)$|\1--break-system-packages \2|; '\
's|^(\tsudo \$\(PIP\) install )(build wheel)$|\1--break-system-packages \2|' \
  makefile

git diff             # expect four changed lines, all adding --break-system-packages
```

### Build and install

```bash
make depend          # the packages in its requirements.txt: numpy, scipy, bottle,
                     # lxml, xmltodict, netconf, ncclient and the sphinx docs set
make install         # builds a wheel, installs it for your user AND for root
```

`make install` deliberately installs **twice** — once as your user, once with
`sudo`. That is not redundant: the optical line runs under `sudo python3`, and
the root-side install is what makes `mnoptical` importable there. If you
replace this with a single user-level `pip install`, `main.py start` will fail
with `ModuleNotFoundError: No module named 'mnoptical'`.

Check both interpreters, from a neutral directory:

```bash
cd /tmp
python3      -c "import mnoptical, os; print('user:', os.path.dirname(mnoptical.__file__))"
sudo python3 -c "import mnoptical, os; print('root:', os.path.dirname(mnoptical.__file__))"
sudo python3 -c "import mininet, mnoptical, bottle; print('optical stack ok')"
```

Expect the root import to resolve under `/usr/local/lib/python3.12/dist-packages`.
The user import may resolve under `~/.local/lib/python3.12/site-packages`;
both being present is the normal outcome of the dual install.

## 6. This repository

```bash
cd ~
git clone https://github.com/allenabishekGithub/inter-domain-automatedNetworking.git
cd inter-domain-automatedNetworking
```

Create one virtual environment for the client tooling and tests:

```bash
python3 -m venv .venv
.venv/bin/pip install -r packet-network/requirements.txt \
                      -r optical-network/requirements.txt
```

This environment covers `pygnmi` (gNMI to the routers), `requests` (the optical
control API) and `pytest`. It deliberately does **not** contain Mininet or
Mininet-Optical: those are system-wide because the privileged interpreter needs
them. See [Which interpreter runs what](#which-interpreter-runs-what).

Check:

```bash
.venv/bin/python -c "import pygnmi, requests, pytest; print('client tooling ok')"
bash scripts/run-tests.sh           # expect 46 + 25 tests, no lab required
```

If the tests pass, the Python side is correct even before anything is deployed.

## 7. Verify the whole stack

One command brings up both packet domains, the optical line, the attachment and
the service:

```bash
sudo scripts/service-up.sh
```

Expect, in order: twelve Containerlab nodes running; the optical control API
answering; `attached to opt-a and opt-b`; `channel 1 configured across 4
ROADMs` with a worst modelled gOSNR near 28.4 dB; both packet domains
configured; a successful ping; and the receiver started.

Then confirm the service is actually carrying traffic:

```bash
.venv/bin/python packet-network/main.py traffic status
```

The `receiver` block should show samples accumulating at roughly 1 Mbit/s with
0% loss. Sender output alone does not establish delivery.

Optionally exercise the optical domain's own decision — moving the live service
to the other wavelength:

```bash
cd optical-network
sudo python3 main.py status                  # carrying_channels: [1]
sudo python3 main.py configure --channel 2   # retune
sudo python3 main.py status                  # carrying_channels: [2]
```

Traffic should keep flowing across the change, losing roughly 90-100 ms of
delivery in the receiver interval that spans it.

Optionally exercise a repair end to end:

```bash
V=.venv/bin/python
$V packet-network/main.py impair down --domain packet-a     # break the primary
$V packet-network/main.py path show   --domain packet-a     # primary_degraded: true
$V packet-network/main.py path backup --domain packet-a     # switch
$V packet-network/main.py traffic status                    # delivery resumes
$V packet-network/main.py impair up   --domain packet-a
$V packet-network/main.py path primary --domain packet-a
```

Tear down when finished:

```bash
sudo scripts/service-down.sh
```

## Required upstream edits

Three edits across two projects. All are consequences of Ubuntu 24.04, not of
anything in this repository, and all were verified to reproduce exactly against
pristine upstream checkouts.

### Edit 1 — `mininet/Makefile`

```diff
 install: install-mnexec install-manpages
 #	This seems to work on all pip versions
 	$(PYTHON) -m pip uninstall -y mininet || true
-	$(PYTHON) -m pip install .
+	$(PYTHON) -m pip install --break-system-packages .
```

**Why.** `make install` installs Mininet into the system interpreter. On 24.04
that interpreter is externally managed, so pip refuses and the install fails.

**Why not a virtual environment instead.** Mininet has to be importable by the
root interpreter that builds network namespaces, alongside `mnexec` and the
system Open vSwitch. Putting it in a venv means maintaining a privileged venv
and pointing every `sudo` invocation at it. `--break-system-packages` is the
smaller change for a dedicated lab machine — and it does write into system
Python, so use a machine you are willing to treat as a lab.

### Edit 2 — `mininet/util/install.sh`

```diff
         $install gcc make socat psmisc xterm ssh iperf telnet \
-                 ethtool help2man $pf pylint pep8 \
+                 ethtool help2man $pf pylint \
                  net-tools \
                  ${PYPKG}-pexpect ${PYPKG}-tk
```

**Why.** `pep8` was renamed to `pycodestyle` years ago and no longer exists in
Ubuntu's archive (`apt-cache policy pep8` → `Candidate: (none)`). `apt install`
fails on the unknown package, which aborts the dependency phase.

**Why it matters beyond the error message.** The installer runs `-n` before
`-v`. When `-n` dies here, Open vSwitch is never installed, but the script has
already produced pages of successful output — so the failure reads as noise and
the missing `ovs-vsctl` only surfaces much later, when the optical line will not
start. That is the reason [step 4](#4-open-vswitch) verifies Open vSwitch on its
own rather than trusting the installer.

`pep8` is only a lint dependency; nothing in Mininet's runtime uses it. If you
want the modern equivalent, `sudo apt install pycodestyle` after the fact.

### Edit 3 — `mininet-optical/makefile`

```diff
 install: dist
-	$(PIP) install --upgrade --verbose dist/*.whl
-	sudo $(PIP) install --upgrade --verbose dist/*.whl
+	$(PIP) install --break-system-packages --upgrade --verbose dist/*.whl
+	sudo $(PIP) install --break-system-packages --upgrade --verbose dist/*.whl

 depend: requirements.txt
-	sudo $(PIP) install -r requirements.txt
-	sudo $(PIP) install build wheel
+	sudo $(PIP) install --break-system-packages -r requirements.txt
+	sudo $(PIP) install --break-system-packages build wheel
```

**Why.** Same PEP 668 guard as edit 1, on both the dependency step and the
wheel install. Note that the `install` target already installed twice by
design — user and root — and both invocations need the flag; patching only one
leaves `mnoptical` missing from whichever interpreter you did not fix, and the
symptom (`main.py start` fails, `main.py configure` works) is confusing.

### Reapplying after an upstream update

These edits live in working trees outside this repository, so a `git pull`
there can silently revert them. Keep them as patches:

```bash
cd ~/mininet         && git diff > ~/mininet-ubuntu2404.patch
cd ~/mininet-optical && git diff > ~/mininet-optical-ubuntu2404.patch
```

and reapply with `git apply` after updating. If an edit no longer applies,
upstream has changed that line — re-derive it rather than forcing it.

## Which interpreter runs what

This trips people up more than anything else in the install, so it is worth
stating plainly. There are two interpreters and they have different jobs:

| Runs | Interpreter | Needs |
|---|---|---|
| `optical-network/main.py start` | `sudo python3` (system) | `mininet`, `mnoptical`, root, Open vSwitch |
| `optical-network/main.py configure` / `monitor` / `status` | either | `requests` only — talks HTTP to the running line |
| `packet-network/main.py *` | `.venv/bin/python` | `pygnmi` |
| `scripts/run-tests.sh` | `.venv/bin/python` | `pytest` |
| `sudo scripts/service-up.sh` | both | uses each for its own part |

The virtual environment does **not** make Mininet available to `sudo python3`,
and installing Mininet system-wide does **not** put `pygnmi` in it. Both are
needed, separately. `service-up.sh` accepts `VENV_PYTHON` and
`EMULATOR_PYTHON` if your paths differ from the defaults.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `error: externally-managed-environment` during a `make install` | PEP 668 guard | Edit 1 or 3 was not applied, or was applied to only one of the two pip lines. |
| `E: Unable to locate package pep8` | Obsolete package | Edit 2. |
| `ovs-vsctl: command not found`, or the optical line fails to start switches | The installer's `-n` phase failed before `-v` ran | [Step 4](#4-open-vswitch); install Open vSwitch directly. |
| `ModuleNotFoundError: No module named 'mnoptical'` under `sudo` | Only the user-level install happened | Re-run `make install` in `~/mininet-optical` with edit 3 applied; verify with `sudo python3 -c "import mnoptical"`. |
| `import mininet` resolves to `~/mininet/mininet` | You are inside the source tree; Python prefers the working directory | Re-check from `/tmp`. Not a real fault. |
| `permission denied while trying to connect to the Docker daemon` | Group membership not active in this shell | `newgrp docker`, or log out and back in. |
| `port 8080 is already serving an optical line` | A previous line is still running | `sudo scripts/service-down.sh`; confirm with `ss -ltn \| grep 8080`. |
| `the optical line started but opt-a has no attachment port` | The packet topology was not up when the line started | Deploy the packet topology first, then start the line with `--attach`. |
| Routers deploy but `configure` times out | SR Linux gNMI not ready yet | It retries three times; if it still fails, give the nodes longer and re-run — the routers take a while on a small VM. |
| First ping after attachment loses packets | The attachment bridges are still learning addresses | Probe again. Expected, not a fault. |
| `ssl_target_name_override is applied` on stderr | The lab nodes use self-signed certificates | Informational. It is on stderr and does not affect JSON output on stdout. |

## Uninstalling

To remove the lab but keep the tooling:

```bash
sudo scripts/service-down.sh
```

To remove the emulator packages as well:

```bash
sudo pip uninstall -y mininet mininet-optical    # add --break-system-packages if pip refuses
pip  uninstall -y mininet-optical                # the user-side copy
sudo apt remove -y openvswitch-switch
rm -rf ~/mininet ~/mininet-optical
```

Remember there are two copies of `mnoptical` — one system-wide and one under
`~/.local` — so removing only one leaves the other importable.

Docker, Containerlab and the pulled images are left alone by the above; remove
them with `sudo apt remove docker-ce ...`, the Containerlab installer's own
instructions, and `docker image rm` respectively.
