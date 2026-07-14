"""Google Sheets 결과 기록을 위한 작은 어댑터."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import gspread
from google.oauth2.service_account import Credentials


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def append_result(secrets: Any, result: dict[str, Any]) -> tuple[bool, str]:
    """시크릿이 올바르면 한 행을 추가하고, 사용자에게 보여줄 상태를 돌려준다."""
    try:
        service_account = dict(secrets["gcp_service_account"])
        game_settings = secrets["game"]
        spreadsheet_id = game_settings["spreadsheet_id"]
        worksheet_name = game_settings.get("worksheet", "results")
    except Exception:
        return False, "Google Sheets 시크릿이 아직 설정되지 않았습니다. README의 설정 예시를 확인해 주세요."

    try:
        credentials = Credentials.from_service_account_info(service_account, scopes=SCOPES)
        client = gspread.authorize(credentials)
        worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            result["record_code"],
            result["name"],
            result["department"],
            result["main_score"],
            result["main_seconds"],
            result["bonus_score"],
            result["bonus_streak"],
            result["bonus_attempts"],
            result["main_risk_used"],
            result["main_risk_success"],
            result["main_choices"],
        ]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True, "기록이 Google Sheets에 저장되었습니다."
    except Exception:
        return False, "Google Sheets 기록 중 오류가 발생했습니다. 스프레드시트 ID와 서비스 계정 공유 권한을 확인해 주세요."
