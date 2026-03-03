#!/usr/bin/env bash
# =============================================================================
# draw.sh — 批量生成 Stackbar 对比图
#
# 输出目录结构:
#   expr/plots/
#   ├── mode1_all/            # Mode 1: 全量实例（不过滤）
#   │   ├── stackbar_python.pdf
#   │   ├── stackbar_java11.pdf
#   │   └── stackbar_nodejs14.pdf
#   ├── mode2_redos_claimed/  # Mode 2: 工具报告为 ReDoS（-r）
#   │   ├── stackbar_python.pdf
#   │   ├── stackbar_java11.pdf
#   │   └── stackbar_nodejs14.pdf
#   ├── mode3_strict_tp/      # Mode 3: 严格 TP（-v，按引擎验证）
#   │   ├── stackbar_python.pdf
#   │   ├── stackbar_java11.pdf
#   │   └── stackbar_nodejs14.pdf
#   └── mode4_union_tp/       # Mode 4: 并集 TP（-v -u，按引擎验证）
#       ├── stackbar_python.pdf
#       ├── stackbar_java11.pdf
#       └── stackbar_nodejs14.pdf
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRAW_PY="${SCRIPT_DIR}/expr/draw_cactus.py"
# DATA_DIR="${SCRIPT_DIR}/expr/results"
# OUT_ROOT="${SCRIPT_DIR}/expr/plots"
DATA_DIR="${SCRIPT_DIR}/expr/results-csrru"
OUT_ROOT="${SCRIPT_DIR}/expr/plots-csrru"

ENGINES=("python" "java11" "nodejs14")

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_section() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

log_done() {
    echo -e "  ${GREEN}✔${NC} $1"
}

# 创建所有输出目录
mkdir -p \
    "${OUT_ROOT}/mode1_all" \
    "${OUT_ROOT}/mode2_redos_claimed" \
    "${OUT_ROOT}/mode3_strict_tp" \
    "${OUT_ROOT}/mode4_union_tp"

# =============================================================================
# Mode 1: 全量实例（不过滤，不验证）
# 命令: python3 draw_cactus.py -d ./expr/results -p stackbar
# 注意: Mode 1/2 与引擎无关，但为保持结构一致，对每个引擎均生成一份
# =============================================================================
log_section "Mode 1: All Instances (无过滤)"

for engine in "${ENGINES[@]}"; do
    out="${OUT_ROOT}/mode1_all/stackbar_${engine}.pdf"
    echo -e "  [${YELLOW}${engine}${NC}] → ${out}"
    python3 "${DRAW_PY}" \
        -d "${DATA_DIR}" \
        -p stackbar \
        -o "${out}"
    log_done "${engine} 完成"
done

# =============================================================================
# Mode 2: ReDoS Claimed（工具声称是 ReDoS，-r 过滤）
# 命令: python3 draw_cactus.py -d ./expr/results -p stackbar -r
# =============================================================================
log_section "Mode 2: ReDoS Claimed (-r)"

for engine in "${ENGINES[@]}"; do
    out="${OUT_ROOT}/mode2_redos_claimed/stackbar_${engine}.pdf"
    echo -e "  [${YELLOW}${engine}${NC}] → ${out}"
    python3 "${DRAW_PY}" \
        -d "${DATA_DIR}" \
        -p stackbar \
        -r \
        -o "${out}"
    log_done "${engine} 完成"
done

# =============================================================================
# Mode 3: Strict TP（严格按引擎验证，-v，不开并集）
# 命令: python3 draw_cactus.py -d ./expr/results -v ./expr/results/{engine} -p stackbar
# =============================================================================
log_section "Mode 3: Strict TP (按引擎验证，-v)"

for engine in "${ENGINES[@]}"; do
    verify_dir="${DATA_DIR}/${engine}"
    out="${OUT_ROOT}/mode3_strict_tp/stackbar_${engine}.pdf"
    echo -e "  [${YELLOW}${engine}${NC}] verify_dir=${verify_dir} → ${out}"
    python3 "${DRAW_PY}" \
        -d "${DATA_DIR}" \
        -v "${verify_dir}" \
        -p stackbar \
        -o "${out}"
    log_done "${engine} 完成"
done

# =============================================================================
# Mode 4: Union TP（并集验证，-v -u）
# 命令: python3 draw_cactus.py -d ./expr/results -v ./expr/results/{engine} -p stackbar -u
# =============================================================================
log_section "Mode 4: Union TP (并集验证，-v -u)"

for engine in "${ENGINES[@]}"; do
    verify_dir="${DATA_DIR}/${engine}"
    out="${OUT_ROOT}/mode4_union_tp/stackbar_${engine}.pdf"
    echo -e "  [${YELLOW}${engine}${NC}] verify_dir=${verify_dir} → ${out}"
    python3 "${DRAW_PY}" \
        -d "${DATA_DIR}" \
        -v "${verify_dir}" \
        -p stackbar \
        -u \
        -o "${out}"
    log_done "${engine} 完成"
done

# =============================================================================
# 完成汇总
# =============================================================================
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  所有图表生成完毕！${NC}"
echo -e "${GREEN}  输出目录: ${OUT_ROOT}${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "目录结构:"
find "${OUT_ROOT}" -name "*.pdf" | sort | sed 's|^|  |'
