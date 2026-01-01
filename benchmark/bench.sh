#!/bin/bash
# Benchmark: zpdf vs mutool on PDF/UA Reference Suite
# Compares reading order and speed

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ZPDF="$SCRIPT_DIR/../zig-out/bin/zpdf"
RESULTS_DIR="$SCRIPT_DIR/results"

mkdir -p "$RESULTS_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}PDF/UA Reference Suite Benchmark${NC}"
echo "=================================="
echo ""

# Collect all PDFs
PDFS=("$SCRIPT_DIR"/*.pdf)
echo "Found ${#PDFS[@]} PDF files"
echo ""

# Summary arrays
declare -a ZPDF_TIMES
declare -a MUTOOL_TIMES
declare -a FILE_NAMES

for pdf in "${PDFS[@]}"; do
    name=$(basename "$pdf")
    echo -e "${YELLOW}Processing: $name${NC}"

    # --- ZPDF extraction ---
    zpdf_out="$RESULTS_DIR/${name%.pdf}.zpdf.txt"
    zpdf_tagged_out="$RESULTS_DIR/${name%.pdf}.zpdf-tagged.txt"

    # Stream order (default, fast)
    start=$(python3 -c 'import time; print(time.time())')
    "$ZPDF" extract "$pdf" > "$zpdf_out" 2>/dev/null || true
    end=$(python3 -c 'import time; print(time.time())')
    zpdf_time=$(python3 -c "print(f'{($end - $start) * 1000:.2f}')")

    # Tagged/structure tree order
    start_tagged=$(python3 -c 'import time; print(time.time())')
    "$ZPDF" extract --tagged "$pdf" > "$zpdf_tagged_out" 2>/dev/null || true
    end_tagged=$(python3 -c 'import time; print(time.time())')
    zpdf_tagged_time=$(python3 -c "print(f'{($end_tagged - $start_tagged) * 1000:.2f}')")

    # --- MuTool extraction ---
    mutool_out="$RESULTS_DIR/${name%.pdf}.mutool.txt"

    start=$(python3 -c 'import time; print(time.time())')
    mutool convert -F text -o "$mutool_out" "$pdf" 2>/dev/null || true
    end=$(python3 -c 'import time; print(time.time())')
    mutool_time=$(python3 -c "print(f'{($end - $start) * 1000:.2f}')")

    # --- Stats ---
    zpdf_chars=$(wc -c < "$zpdf_out" 2>/dev/null | tr -d ' ')
    zpdf_tagged_chars=$(wc -c < "$zpdf_tagged_out" 2>/dev/null | tr -d ' ')
    mutool_chars=$(wc -c < "$mutool_out" 2>/dev/null | tr -d ' ')

    echo "  zpdf (stream):   ${zpdf_time}ms, ${zpdf_chars} chars"
    echo "  zpdf (tagged):   ${zpdf_tagged_time}ms, ${zpdf_tagged_chars} chars"
    echo "  mutool:          ${mutool_time}ms, ${mutool_chars} chars"

    # Speedup
    if [ "$mutool_time" != "0.00" ]; then
        speedup=$(python3 -c "print(f'{float($mutool_time) / max(0.01, float($zpdf_time)):.2f}')")
        echo -e "  ${GREEN}speedup: ${speedup}x${NC}"
    fi
    echo ""

    ZPDF_TIMES+=("$zpdf_time")
    MUTOOL_TIMES+=("$mutool_time")
    FILE_NAMES+=("$name")
done

# Summary
echo -e "${BLUE}Summary${NC}"
echo "======="
echo ""

# Calculate totals
total_zpdf=$(python3 -c "print(f'{sum([float(x) for x in \"${ZPDF_TIMES[*]}\".split()]):.2f}')")
total_mutool=$(python3 -c "print(f'{sum([float(x) for x in \"${MUTOOL_TIMES[*]}\".split()]):.2f}')")
overall_speedup=$(python3 -c "print(f'{float($total_mutool) / max(0.01, float($total_zpdf)):.2f}')")

echo "Total zpdf:   ${total_zpdf}ms"
echo "Total mutool: ${total_mutool}ms"
echo -e "${GREEN}Overall speedup: ${overall_speedup}x${NC}"
echo ""

echo "Results saved to: $RESULTS_DIR"
echo ""
echo "To compare reading order differences:"
echo "  diff $RESULTS_DIR/<file>.zpdf-ro.txt $RESULTS_DIR/<file>.mutool.txt"
