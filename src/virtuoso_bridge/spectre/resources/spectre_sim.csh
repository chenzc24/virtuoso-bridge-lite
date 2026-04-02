#!/usr/bin/env csh
# Spectre simulation wrapper script (csh)
#
# Usage: csh spectre_sim.csh <netlist.scs> [spectre_cmd] [extra_args...]
#
# Arguments:
#   netlist.scs   - Path to the Spectre netlist file (required)
#   spectre_cmd   - Path or name of the Spectre executable (optional, default: "spectre")
#   extra_args    - Additional arguments passed to spectre (e.g. "-format psfascii")
#
# Environment:
#   Automatically sources Cadence IC618 and Mentor environment scripts
#   on the compute server before running the simulation.
#   Using csh natively so that `source .cshrc.*` works directly.
#
# Exit codes:
#   0 - Simulation completed successfully
#   1 - Missing arguments or file not found
#   3 - Spectre simulation failed

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

if ($#argv < 1) then
    echo "ERROR: Missing required argument: <netlist.scs>"
    echo "Usage: $0 <netlist.scs> [spectre_cmd] [extra_args...]"
    exit 1
endif

set NETLIST = "$argv[1]"
if ($#argv >= 2) then
    set SPECTRE_CMD = "$argv[2]"
else
    set SPECTRE_CMD = "spectre"
endif

# Collect any extra arguments (e.g. "-format psfascii") from argv[3..]
set EXTRA_ARGS = ""
if ($#argv >= 3) then
    set EXTRA_ARGS = ""
    @ i = 3
    while ($i <= $#argv)
        set EXTRA_ARGS = "$EXTRA_ARGS $argv[$i]"
        @ i++
    end
    set EXTRA_ARGS = `echo $EXTRA_ARGS`
endif

# Validate netlist file exists
if (! -f "$NETLIST") then
    echo "ERROR: Netlist file not found: $NETLIST"
    exit 1
endif

# Resolve absolute path of netlist
set NETLIST_DIR = `dirname "$NETLIST"`
set NETLIST_BASE = `basename "$NETLIST"`
cd "$NETLIST_DIR"
set NETLIST_ABS = "`pwd`/$NETLIST_BASE"
set WORK_DIR = `pwd`

echo "=== Spectre Simulation Wrapper ==="
echo "Netlist:     $NETLIST_ABS"
echo "Spectre cmd: $SPECTRE_CMD"
echo "Extra args:  $EXTRA_ARGS"
echo "Work dir:    $WORK_DIR"

# ---------------------------------------------------------------------------
# Environment setup (Cadence IC618 + Mentor)
# ---------------------------------------------------------------------------

# VB_CADENCE_CSHRC and VB_MENTOR_CSHRC are always exported by the Python
# runner, so we can reference them directly here.
# HOSTNAME / LD_LIBRARY_PATH / MANPATH / LM_LICENSE_FILE are likewise
# pre-exported by the runner so the sourced env scripts never see them
# as undefined.
set CADENCE_ENV = "$VB_CADENCE_CSHRC"
set MENTOR_ENV  = "$VB_MENTOR_CSHRC"

if (-f "$CADENCE_ENV") then
    echo "Sourcing Cadence environment: $CADENCE_ENV"
    source "$CADENCE_ENV"
else
    echo "WARNING: Cadence environment script not found: $CADENCE_ENV"
endif

if (-f "$MENTOR_ENV") then
    echo "Sourcing Mentor environment: $MENTOR_ENV"
    source "$MENTOR_ENV"
else
    echo "WARNING: Mentor environment script not found: $MENTOR_ENV"
endif

echo "PATH after environment setup: $PATH"

# ---------------------------------------------------------------------------
# Run Spectre simulation
# ---------------------------------------------------------------------------

echo "Running Spectre simulation..."
echo "Command: $SPECTRE_CMD $EXTRA_ARGS $NETLIST_ABS"
echo "Working directory: $WORK_DIR"

cd "$WORK_DIR"

# Execute Spectre with optional extra arguments and the netlist file
if ("$EXTRA_ARGS" == "") then
    $SPECTRE_CMD "$NETLIST_ABS"
else
    $SPECTRE_CMD $EXTRA_ARGS "$NETLIST_ABS"
endif
set SPECTRE_EXIT = $status

if ($SPECTRE_EXIT != 0) then
    echo "ERROR: Spectre simulation failed with exit code $SPECTRE_EXIT"
    exit 3
endif

echo "=== Spectre simulation completed successfully ==="
exit 0
