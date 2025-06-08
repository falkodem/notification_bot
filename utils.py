import datetime
from dateutil.relativedelta import relativedelta

from collections import namedtuple
from consts import DAY_MONTH_INFO, MONTH_INFO, PERIODICITY_INFO, MONTH_TO_NOMINATIVE, PERIODICITY_INFO_REVERSE

validation_res = namedtuple('validation_res', ['is_valid', 'result', 'error_message'])

def format_notifications_for_response(notifications):
    """
    Formats the notifications for better readability.
    """
    response = "📋 Ваши заметки:\n\n"
    for notification in notifications:
        response += (f"{notification[2]}. <b>{notification[3]}</b>\n"
                     f"\tДата: {notification[4][:-3]}\n"
                     f"\tПериодичность: {PERIODICITY_INFO_REVERSE[int(notification[5])]}\n\n")
    return response

def format_notification_oneline(notification):
    """
    Formats a single notification for one-line display.
    """
    return (f"{notification[2]}. <b>{notification[3]}</b> "
            f"({notification[4][:-3]}, {PERIODICITY_INFO_REVERSE[int(notification[5])]})")
    

def format_user_input(parts):
    """
    Validates the user input parts.
    """
    try:
        parts_validation = validate_structure(parts)

        if not parts_validation.is_valid:
            return parts_validation
        
        name, date, time, periodicity  = parts_validation.result
        name_validation = validate_name_format(name)
        if not name_validation.is_valid:
            return name_validation
        
        date_validation = validate_date(date)
        if not date_validation.is_valid:
            return date_validation
        
        time_validation = validate_time_format(time)
        if not time_validation.is_valid:
            return time_validation

        periodicity_validation = validate_periodicity_format(periodicity)
        if not periodicity_validation.is_valid:
            return periodicity_validation
        

        notification_full_date = datetime.datetime(
            year = datetime.datetime.now().year, 
            month = date_validation.result[1], 
            day = date_validation.result[0], 
            hour=time_validation.result[0], 
            minute=time_validation.result[1])
        
        if notification_full_date <= datetime.datetime.now():
            notification_full_date = notification_full_date.replace(year=notification_full_date.year + 1)
        notification_full_date = notification_full_date.strftime("%Y-%m-%d %H:%M:%S")

        return validation_res(True, (name_validation.result, notification_full_date, periodicity_validation.result), None)
    except Exception as e:
        return validation_res(False, None, f"Произошла ошибка при обработке данных: {str(e)}. Пожалуйста, проверь формат ввода.")


def validate_structure(user_input):
        parts = [elem.strip() for elem in user_input.split(";")]

        if len(parts) < 3 or len(parts) > 4 :
            return validation_res(False, None, "Пожалуйста, введи данные в формате: <b>Название; Дата; Время уведомления; (Опционально) Периодичность</b>.")

        if len(parts) == 3:
            parts.append("один раз")
        
        return validation_res(True, parts, None)

def validate_date(date_str):
    """
    Validates the date format. Expected format: 'DD Month' (e.g., '15 September').
    """
    if len(date_str.split(' ')) != 2:
        return validation_res(False, None, "Проверь формат ввода даты события. Ожидается формат: 'ДД Месяц' (например, '15 Сентября').")
    
    day, month = date_str.split(' ')

    if not day.isdigit():
        return validation_res(False, None, f"Такого дня в месяце не существует: {day}. Попробуй еще раз.")
    
    day, month = int(day), MONTH_TO_NOMINATIVE.get(month.lower(), month).capitalize()

    if month not in DAY_MONTH_INFO:
        return validation_res(False, None, f"Не удалось считать месяц. Введи месяц из списка: {', '.join(DAY_MONTH_INFO.keys())}.")
    
    if day == 29 and month == 'Февраль' and datetime.datetime.now().year % 4 != 0:
        return validation_res(False, None, "В этом году 29 февраля не будет")
    
    if day < 1 or day > DAY_MONTH_INFO[month]:
        return validation_res(False, None, f"Количество дней в этом месяце - {DAY_MONTH_INFO[month]}. Проверь дату и попробуй еще раз.")
    
    return validation_res(True, (day, MONTH_INFO.index(month.capitalize())+1), None)

def validate_name_format(name_str):
    """
    Validates the name format.
    """
    name_str = name_str.strip()
    if not name_str or len(name_str) == 0:
        return validation_res(False, None, "Название события не может быть пустым.")
    
    name_str = name_str.strip()

    if len(name_str) > 100:
        return validation_res(False, None,"Не могу принять такое длинное название заметки, постарайся его сократь.")
    return validation_res(True, name_str.capitalize(), None)

def validate_time_format(time_str):
    """
    Validates the time format. Expected format: 'HH:MM' or HH MM (e.g., '13:00' or '13 00').
    """
    if not time_str or len(time_str.strip()) == 0:
        return validation_res(False, None, "Время уведомления не может быть пустым.")
    
    time_str = time_str.strip()
    if time_str[0] != '0' and len(time_str) == 4:
        time_str = '0' + time_str

    if len(time_str) != 5 or time_str[2] not in [':', ' ']:
        return validation_res(False, None, "Неверный формат времени. Используй формат 'HH:MM' или 'HH MM'.")

    if time_str[2] == ' ':
        time_str = time_str.replace(' ', ':')
    try:
        hour, minute = map(int, time_str.split(':'))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return validation_res(False, None, "Часы должны быть от 00 до 23, а минуты от 00 до 59.")
    except ValueError:
        return validation_res(False, None, "Проверь формат времени. Используй 'HH:MM'.")
    
    # Convert hour and minute to a time string suitable for a datetime column (e.g., 'HH:MM:00')
    return validation_res(True, (hour, minute), None)

def validate_periodicity_format(periodicity_str):
    """
    Validates the periodicity format.
    """
    if len(periodicity_str.strip()) == 0:
        periodicity = 'один раз'
    else:
        periodicity = periodicity_str.strip().lower()
        if periodicity not in PERIODICITY_INFO:
            return validation_res(False, None, "Неверная периодичность для уведомления. Доступные: один раз, ежедневно, еженедельно, ежемесячно или ежегодно.")
        
    return validation_res(True, PERIODICITY_INFO[periodicity], None)  

def check_if_time_is_now(notification_datetime):
    notification_dt = datetime.datetime.strptime(notification_datetime, "%Y-%m-%d %H:%M:%S")
    now = datetime.datetime.now().replace(second=0, microsecond=0)
    return notification_dt == now

def update_notification_datetime(notification_datetime, periodicity):
    """
    Updates the notification datetime based on the periodicity.
    """
    notification_dt = datetime.datetime.strptime(notification_datetime, "%Y-%m-%d %H:%M:%S")
    
    if periodicity == 1:  # daily
        notification_dt += datetime.timedelta(days=1)
    elif periodicity == 2:  # weekly
        notification_dt += datetime.timedelta(weeks=1)
    elif periodicity == 3:  # monthly
        notification_dt += relativedelta(months=1)
    elif periodicity == 4:  # yearly
        notification_dt += relativedelta(years=1)

    return notification_dt.strftime("%Y-%m-%d %H:%M:%S")

