import logging

# Cấu hình logging hệ thống
# YÊU CẦU 2 - SỬA LỖI: Đổi level từ WARNING sang INFO
# để hệ thống hiển thị đầy đủ các mức log từ INFO trở đi
logging.basicConfig(
    level=logging.INFO,  # ĐÃ SỬA: Từ WARNING -> INFO
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def get_shipping_rate(method: str, distance: int) -> float:
    """Trả về chi phí vận chuyển cơ sở dựa trên phương thức và khoảng cách"""
    logger.info(f"Đang tính phí giao hàng cho phương thức {method} với khoảng cách {distance} km")

    # YÊU CẦU 2 - SỬA LỖI RUNTIME: Thay vì chỉ log rồi return 0.0,
    # phải raise ValueError để chặn dữ liệu sai ngay từ đầu (Clean Code)
    if distance <= 0:
        logger.error("Khoảng cách vận chuyển không được nhỏ hơn hoặc bằng 0")
        raise ValueError("Distance must be positive")  # ĐÃ SỬA: raise thay vì return 0.0

    # Xác định phí cơ sở theo phương thức vận chuyển
    if method == "standard":
        base_rate = 15000
    elif method == "express":
        base_rate = 30000
    elif method == "next_day":
        base_rate = 50000
    else:
        base_rate = 20000

    # Phụ thu đường xa nếu khoảng cách từ 20km trở lên
    # YÊU CẦU 2 - SỬA LỖI LOGIC: Đổi base_rate = 10000 thành base_rate += 10000
    # để CỘNG THÊM phụ thu vào phí hiện tại, không phải gán đè lên
    if distance >= 20:
        base_rate += 10000  # ĐÃ SỬA: Từ = 10000 -> += 10000

    return base_rate


def calculate_final_shipping(weight: float, distance: int, method: str) -> float:
    """Tính tổng chi phí vận chuyển cuối cùng dựa trên trọng lượng hàng hóa"""
    if weight < 0:
        raise ValueError("Trọng lượng hàng hóa không được âm")

    base_rate = get_shipping_rate(method, distance)

    # Giả sử phí tăng thêm 2,000đ cho mỗi kg hàng hóa
    total_cost = base_rate + (weight * 2000)

    logger.warning(f"Kết quả: Tổng phí vận chuyển = {total_cost}")
    return total_cost


# Khúc code chạy thử
if __name__ == "__main__":
    # Case 1: Kiểm tra phụ thu đường xa (distance=25 >= 20, method=express)
    # Kết quả đúng: base_rate = 30000 + 10000 = 40000, total = 40000 + (3.5 * 2000) = 47000
    result1 = calculate_final_shipping(3.5, 25, "express")
    print(f"Case 1 - express, 25km, 3.5kg: {result1} VND")

    # Case 2: Kiểm tra lỗi dữ liệu đầu vào (distance=-5)
    # Kết quả đúng: raise ValueError
    try:
        calculate_final_shipping(2.0, -5, "standard")
    except ValueError as e:
        print(f"Case 2 - Bắt được ngoại lệ hợp lệ: {e}")
