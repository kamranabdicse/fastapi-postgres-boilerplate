""" Message codes for api responses """


class MessageCodes:
    # main codes start from 0
    successful_operation = 0
    internal_error = 1
    not_found = 2
    bad_request = 3
    input_error = 4
    operation_failed = 5
    incorrect_email_or_password = 6
    inactive_user = 7
    permisionError = 8,
    invalid_token = 9
    # services code start from 1001

    messages_names = {
        0: "Successful Operation",
        1: "Internal Error",
        2: "Not Found",
        3: "Bad Request",
        4: "Input Error",
        5: "Operation Failed",
        6: "Invalid Email Or Password",
        7: "Inactive User",
        8: "Dont Have Access",
        9: "Invalid Token",

    }

    persian_message_names = {
        0: "عملیات موفق",
        1: "خطای داخلی",
        2: "پیدا نشد",
        3: "درخواست نا‌معتبر",
        4: "ورودی نامعتبر",
        5: "عملیات ناموفق",
        6: "ایمیل یا پسورد نامعتبر",
        7: "یوزر غیرفعال",
        8: "سظح دسترسی غیرمجاز",
        9: "توکن نامعتبر",
    }
