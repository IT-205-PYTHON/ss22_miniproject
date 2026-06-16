"""
energy_monitor.py
-----------------
Smart Energy Monitor — Hệ Thống Giám Sát Tiêu Hao Năng Lượng.

Cấu trúc:
    - show_devices()              : Hiển thị bảng danh sách thiết bị
    - update_indices()            : Cập nhật chỉ số điện tiêu thụ
    - activate_overload_alert()   : Kích hoạt cảnh báo quá tải
    - calculate_energy_financials(): Tính toán tài chính năng lượng
    - main()                      : Hàm điều phối chính

Chạy:
    python energy_monitor.py
"""

import logging
import sys

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_RATE_VND_PER_KWH: int = 3_000          # VND per kWh
OVERLOAD_THRESHOLD_KWH: int = 5_000         # kWh
DISCOUNT_THRESHOLD_KWH: int = 50_000        # kWh
DISCOUNT_RATE: float = 0.03                 # 3 %

STATUS_NORMAL: str = "Normal"
STATUS_OVERLOAD: str = "Overload"

ERR_E01: str = "[ERR-E01] Không tìm thấy mã thiết bị trong hệ thống."
ERR_E02: str = (
    "[ERR-E02] Chỉ số mới không được nhỏ hơn chỉ số cũ. "
    "Vui lòng nhập lại."
)
ERR_E04: str = "[ERR-E04] Thiết bị đã ở trạng thái Overload từ trước."


# ---------------------------------------------------------------------------
# Helper — safe integer input
# ---------------------------------------------------------------------------
def _input_int(prompt: str) -> int:
    """
    Prompt until the user supplies a valid integer.

    Args:
        prompt: Text displayed to the user.

    Returns:
        A valid integer entered by the user.
    """
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            print("  ⚠  Vui lòng nhập một số nguyên hợp lệ.")


def _find_device(devices: list, device_id: str) -> dict | None:
    """
    Search *devices* for the entry whose 'id' matches *device_id*.

    Args:
        devices:   List of device dictionaries.
        device_id: The ID string to search for.

    Returns:
        The matching dict, or None if not found.
    """
    for device in devices:
        if device["id"] == device_id.strip().upper():
            return device
    return None


# ---------------------------------------------------------------------------
# Feature 1 — Display device list
# ---------------------------------------------------------------------------
def show_devices(devices: list) -> None:
    """
    Print all devices in a formatted, column-aligned table.

    Args:
        devices: List of device dictionaries to display.
    """
    if not devices:
        print("\n  [Hệ thống trống] Chưa có thiết bị nào được đăng ký.")
        return

    col_w = {"id": 8, "loc": 24, "old": 12, "new": 12,
             "cons": 14, "status": 10}
    divider = "-" * 78

    print("\n" + divider)
    print(
        f"  {'Mã TB':<{col_w['id']}} {'Vị trí':<{col_w['loc']}} "
        f"{'Chỉ số cũ':>{col_w['old']}} {'Chỉ số mới':>{col_w['new']}} "
        f"{'Tiêu thụ (kWh)':>{col_w['cons']}} {'Trạng thái':<{col_w['status']}}"
    )
    print(divider)

    for dev in devices:
        consumption = dev["new_index"] - dev["old_index"]
        print(
            f"  {dev['id']:<{col_w['id']}} "
            f"{dev['location']:<{col_w['loc']}} "
            f"{dev['old_index']:>{col_w['old']},} "
            f"{dev['new_index']:>{col_w['new']},} "
            f"{consumption:>{col_w['cons']},} "
            f"{dev['status']:<{col_w['status']}}"
        )

    print(divider)
    logger.info("Displayed device list (%d device(s)).", len(devices))


# ---------------------------------------------------------------------------
# Feature 2 — Update energy indices
# ---------------------------------------------------------------------------
def update_indices(devices: list) -> None:
    """
    Collect device ID and new meter readings from the cashier, validate
    them, then update the matching device record in-place.

    Validation rules:
        - Device ID must exist (ERR-E01).
        - new_index >= old_index (ERR-E02, re-prompt loop).
        - Indices must be non-negative integers.

    Args:
        devices: List of device dictionaries to update.
    """
    print("\n--- CẬP NHẬT CHỈ SỐ ĐIỆN TIÊU THỤ ---")
    device_id = input("  Nhập mã thiết bị: ").strip().upper()
    device = _find_device(devices, device_id)

    if device is None:
        print(f"\n  {ERR_E01}")
        logger.warning("Update failed — device not found: %s", device_id)
        return

    # Collect & validate old_index
    while True:
        old_index = _input_int("  Nhập chỉ số cũ: ")
        if old_index >= 0:
            break
        print("  ⚠  Chỉ số phải lớn hơn hoặc bằng 0.")

    # Collect & validate new_index (must be >= old_index)
    while True:
        new_index = _input_int("  Nhập chỉ số mới: ")
        if new_index < 0:
            print("  ⚠  Chỉ số phải lớn hơn hoặc bằng 0.")
            continue
        if new_index < old_index:
            print(f"\n  {ERR_E02}")
            continue
        break

    device["old_index"] = old_index
    device["new_index"] = new_index
    consumption = new_index - old_index

    logger.info(
        "Updated device %s — old: %d, new: %d, consumption: %d kWh.",
        device_id, old_index, new_index, consumption,
    )
    print(
        f"\n  ✔  Cập nhật thành công thiết bị [{device_id}].\n"
        f"     Lượng điện tiêu thụ: {consumption:,} kWh."
    )


# ---------------------------------------------------------------------------
# Feature 3 — Activate overload alert
# ---------------------------------------------------------------------------
def activate_overload_alert(devices: list) -> None:
    """
    Search for a device by ID and switch its status to Overload if its
    consumption exceeds OVERLOAD_THRESHOLD_KWH.

    Error codes:
        ERR-E01: Device not found.
        ERR-E04: Device already in Overload state.

    Args:
        devices: List of device dictionaries to inspect.
    """
    print("\n--- KÍCH HOẠT TRẠNG THÁI CẢNH BÁO QUÁ TẢI ---")
    device_id = input("  Nhập mã thiết bị cần kiểm tra: ").strip().upper()
    device = _find_device(devices, device_id)

    if device is None:
        print(f"\n  {ERR_E01}")
        logger.warning(
            "Alert activation failed — device not found: %s", device_id
        )
        return

    if device["status"] == STATUS_OVERLOAD:
        print(f"\n  {ERR_E04}")
        logger.info(
            "Device %s already in Overload state — no action taken.",
            device_id,
        )
        return

    consumption = device["new_index"] - device["old_index"]

    if consumption > OVERLOAD_THRESHOLD_KWH:
        device["status"] = STATUS_OVERLOAD
        logger.warning(
            "OVERLOAD ALERT — Device %s consumption %d kWh exceeds "
            "threshold %d kWh. Status set to Overload.",
            device_id, consumption, OVERLOAD_THRESHOLD_KWH,
        )
        print(
            f"\n  ⚠  CẢNH BÁO: Thiết bị [{device_id}] tiêu thụ "
            f"{consumption:,} kWh vượt ngưỡng "
            f"{OVERLOAD_THRESHOLD_KWH:,} kWh.\n"
            f"     Trạng thái đã được chuyển sang → Overload."
        )
    else:
        print(
            f"\n  ✔  Thiết bị [{device_id}] tiêu thụ {consumption:,} kWh "
            f"— dưới ngưỡng quá tải. Không cần cảnh báo."
        )
        logger.info(
            "Device %s consumption %d kWh — below threshold, no alert.",
            device_id, consumption,
        )


# ---------------------------------------------------------------------------
# Feature 4 — Financial calculation (returns Tuple)
# ---------------------------------------------------------------------------
def calculate_energy_financials(devices: list) -> tuple:
    """
    Calculate total energy consumption and cost with optional discount.

    Discount rule:
        >= DISCOUNT_THRESHOLD_KWH → DISCOUNT_RATE (3 %)
        <  DISCOUNT_THRESHOLD_KWH → 0 %

    Args:
        devices: List of device dictionaries.

    Returns:
        A tuple of (total_kwh: int, discount_pct: float, total_cost: float).
    """
    total_kwh = sum(
        dev["new_index"] - dev["old_index"] for dev in devices
    )
    gross_cost = total_kwh * BASE_RATE_VND_PER_KWH

    if total_kwh >= DISCOUNT_THRESHOLD_KWH:
        discount_pct = DISCOUNT_RATE
    else:
        discount_pct = 0.0

    total_cost = gross_cost * (1 - discount_pct)

    return (total_kwh, discount_pct, total_cost)


# ---------------------------------------------------------------------------
# Menu display
# ---------------------------------------------------------------------------
def display_main_menu() -> None:
    """Print the main navigation menu to stdout."""
    print("\n" + "=" * 48)
    print("   HỆ THỐNG GIÁM SÁT TIÊU HAO NĂNG LƯỢNG")
    print("=" * 48)
    print("  1. Xem danh sách thiết bị giám sát")
    print("  2. Cập nhật chỉ số điện tiêu thụ")
    print("  3. Kích hoạt trạng thái cảnh báo quá tải")
    print("  4. Tính tổng lượng điện & Chi phí năng lượng")
    print("  5. Thoát chương trình")
    print("=" * 48)


# ---------------------------------------------------------------------------
# Main — dispatcher
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Entry point.

    Initialises sample data, configures logging, and runs the interactive
    CLI loop until the user selects option 5.
    """
    devices: list = [
        {
            "id": "M01",
            "location": "Mechanical Shop A",
            "old_index": 1_200,
            "new_index": 4_500,
            "status": STATUS_NORMAL,
        },
        {
            "id": "M02",
            "location": "Assembly Line B",
            "old_index": 2_300,
            "new_index": 8_500,
            "status": STATUS_OVERLOAD,
        },
        {
            "id": "M03",
            "location": "Packaging Zone C",
            "old_index": 5_000,
            "new_index": 60_000,
            "status": STATUS_NORMAL,
        },
    ]

    logger.info("Smart Energy Monitor started.")

    while True:
        display_main_menu()
        raw = input("  Chọn chức năng (1-5): ").strip()

        try:
            choice = int(raw)
        except ValueError:
            print("  ⚠  Vui lòng nhập một số từ 1 đến 5.")
            continue

        if choice == 1:
            show_devices(devices)

        elif choice == 2:
            update_indices(devices)

        elif choice == 3:
            activate_overload_alert(devices)

        elif choice == 4:
            if not devices:
                print("\n  Chưa có dữ liệu thiết bị để tính toán.")
            else:
                total_kwh, discount_pct, total_cost = (
                    calculate_energy_financials(devices)
                )
                gross = total_kwh * BASE_RATE_VND_PER_KWH
                print("\n--- KẾT QUẢ TÍNH TOÁN CHI PHÍ NĂNG LƯỢNG ---")
                print(f"  Tổng điện tiêu thụ  : {total_kwh:>12,} kWh")
                print(f"  Đơn giá cơ sở       : {BASE_RATE_VND_PER_KWH:>12,} VNĐ/kWh")
                print(f"  Thành tiền gốc      : {gross:>12,.0f} VNĐ")
                print(f"  Chiết khấu áp dụng  : {discount_pct * 100:>11.0f} %")
                print(f"  Tổng tiền sau CK    : {total_cost:>12,.0f} VNĐ")
                logger.info(
                    "Financial report — %d kWh, discount %.0f%%, "
                    "total %.0f VND.",
                    total_kwh, discount_pct * 100, total_cost,
                )

        elif choice == 5:
            logger.info("System shutdown by user.")
            print("\n  Cảm ơn bạn đã sử dụng hệ thống. Tạm biệt!\n")
            sys.exit(0)

        else:
            print("  ⚠  Lựa chọn không hợp lệ. Vui lòng chọn từ 1 đến 5.")


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
