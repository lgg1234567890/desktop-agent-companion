# -*- coding: utf-8 -*-
"""
农历转换工具（纯Python实现，覆盖1900-2100年）
"""

# 农历数据表：1900-2100年
# 每个数字为16进制：前4位=闰月月份(0无闰月)，后12位=每月大小(1=30天,0=29天)
# 有闰月时，闰月大小在额外位
_LUNAR_INFO = [
    0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,  # 1900-1909
    0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,  # 1910-1919
    0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,  # 1920-1929
    0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,  # 1930-1939
    0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,  # 1940-1949
    0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5b0, 0x14573, 0x052b0, 0x0a9a8, 0x0e950, 0x06aa0,  # 1950-1959
    0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,  # 1960-1969
    0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b6a0, 0x195a6,  # 1970-1979
    0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,  # 1980-1989
    0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,  # 1990-1999
    0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,  # 2000-2009
    0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,  # 2010-2019
    0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,  # 2020-2029
    0x05aa0, 0x076a3, 0x096d0, 0x04afb, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,  # 2030-2039
    0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,  # 2040-2049
    0x14b63, 0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6, 0x0ea50, 0x06b20, 0x1a6c4, 0x0aae0,  # 2050-2059
    0x0a2e0, 0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0, 0x0a6d0, 0x055d4,  # 2060-2069
    0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50, 0x055a0, 0x0aba4, 0x0a5b0, 0x052b0,  # 2070-2079
    0x0b273, 0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x14b55, 0x04b60, 0x0a570, 0x054e4, 0x0d160,  # 2080-2089
    0x0e968, 0x0d520, 0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a2d0, 0x0d150, 0x0f252,  # 2090-2099
    0x0d520,  # 2100
]

# 天干地支
_TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
_SHENG_XIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# 农历月份名称
_LUNAR_MONTHS = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]

# 农历日期名称
_LUNAR_DAYS = [
    "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
]


def _leap_month(year):
    """获取该年闰月月份，0表示无闰月"""
    return _LUNAR_INFO[year - 1900] & 0xf


def _leap_days(year):
    """获取该年闰月天数"""
    if _leap_month(year):
        return 30 if (_LUNAR_INFO[year - 1900] & 0x10000) else 29
    return 0


def _month_days(year, month):
    """获取该年某月（非闰月）的天数"""
    return 30 if (_LUNAR_INFO[year - 1900] & (0x10000 >> month)) else 29


def _year_days(year):
    """获取该年总天数"""
    total = 348  # 12 * 29
    for i in range(1, 13):
        total += _month_days(year, i) - 29
    total += _leap_days(year)
    return total


def solar_to_lunar(date):
    """
    阳历转农历
    date: datetime.date 对象
    返回 dict: {year, month, day, is_leap, year_name, shengxiao, month_name, day_name}
    """
    import datetime
    # 基准：1900年1月31日 = 农历1900年正月初一
    base = datetime.date(1900, 1, 31)
    offset = (date - base).days

    year = 1900
    while year < 2101 and offset > 0:
        days = _year_days(year)
        if offset < days:
            break
        offset -= days
        year += 1

    leap = _leap_month(year)
    is_leap = False
    month = 1

    while month < 13 and offset > 0:
        if leap > 0 and month == leap + 1 and not is_leap:
            # 闰月
            month -= 1
            is_leap = True
            days = _leap_days(year)
        else:
            days = _month_days(year, month)

        if offset < days:
            break
        offset -= days

        if is_leap and month == leap:
            is_leap = False
        month += 1

    day = offset + 1

    # 天干地支年
    year_idx = (year - 1900 + 36) % 60  # 1900年是庚子年
    gan = _TIAN_GAN[year_idx % 10]
    zhi = _DI_ZHI[year_idx % 12]
    shengxiao = _SHENG_XIAO[(year - 1900) % 12]

    month_name = ("闰" if is_leap else "") + _LUNAR_MONTHS[month - 1] + "月"
    day_name = _LUNAR_DAYS[day - 1]

    return {
        "year": year,
        "month": month,
        "day": day,
        "is_leap": is_leap,
        "year_name": f"{gan}{zhi}年",
        "shengxiao": shengxiao,
        "month_name": month_name,
        "day_name": day_name,
        "full": f"{gan}{zhi}年（{shengxiao}年）{month_name}{day_name}",
    }


def get_lunar_today():
    """获取今天的农历信息字符串"""
    import datetime
    today = datetime.date.today()
    lunar = solar_to_lunar(today)
    return lunar["full"]


if __name__ == "__main__":
    import datetime
    today = datetime.date.today()
    print(f"阳历: {today.strftime('%Y年%m月%d日')}")
    print(f"农历: {get_lunar_today()}")
