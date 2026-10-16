"""Synthetic records matching the user's layout; no business workbook is read."""

import io
import sys

from openpyxl import Workbook

HEADERS = ["日期", "姓名", "公司", "职位", "联系电话", "记录", "链接"]
RESUME_URL = "https://example.com/resume?reference=" + "synthetic" * 50


def workbook_bytes():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "候选人"
    sheet.append([])
    sheet.append(HEADERS)
    sheet.append(
        [
            "2026.05.22",
            "合成模板人才",
            "合成模板公司",
            "招聘经理",
            "00123456789",
            "合成模板历史沟通",
            "查看简历",
        ]
    )
    sheet["G3"].hyperlink = RESUME_URL
    sheet["E3"].hyperlink = "https://example.com/phone-display-must-survive"
    sheet.append(["", "合成无日期人才", "", "", "synthetic-phone", "", "javascript:alert(1)"])
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


if __name__ == "__main__":
    sys.stdout.buffer.write(workbook_bytes())
