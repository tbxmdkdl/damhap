from __future__ import annotations

import html
import random
import time
import uuid
from pathlib import Path

import streamlit as st

from scenario_data import BOSS_CHALLENGES, FLOORS
from sheets_client import append_result


APP_DIR = Path(__file__).parent
ASSET_DIR = APP_DIR / "assets"
TOTAL_SCENES = sum(len(floor["scenes"]) for floor in FLOORS)
DEPARTMENTS = ["전략기획", "전략투자", "브랜드성장", "기타"]


st.set_page_config(
    page_title="담합의 탑",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def apply_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #101319;
            --panel: #1b2230;
            --panel-2: #252f40;
            --paper: #f5f2e9;
            --yellow: #ffd44d;
            --red: #e55454;
            --green: #54c58d;
            --blue: #76b9e8;
        }
        .stApp { background: var(--ink); }
        .block-container { max-width: 1080px; padding-top: 1.5rem; padding-bottom: 3rem; }
        #MainMenu, header, footer { visibility: hidden; }
        h1, h2, h3, p, label, .stMarkdown, .stCaption, .stTextInput, .stSelectbox {
            font-family: "Courier New", "Malgun Gothic", monospace !important;
        }
        h1 { color: var(--yellow); border-bottom: 4px solid var(--yellow); padding-bottom: 0.45rem; }
        h2, h3 { color: var(--paper); }
        .pixel-panel {
            border: 3px solid var(--paper);
            box-shadow: 6px 6px 0 #000;
            background: var(--panel);
            padding: 1rem 1.1rem;
            margin: 0.55rem 0 1rem;
        }
        .tower-frame {
            min-height: 245px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: repeating-linear-gradient(0deg, #20293a 0 2px, #18202e 2px 4px);
            border: 4px solid var(--yellow);
            box-shadow: 8px 8px 0 #000;
            color: var(--yellow);
            font-size: 1.4rem;
            font-weight: 700;
            text-align: center;
        }
        .sprite-placeholder {
            min-height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 3px solid currentColor;
            background: #0b0e14;
            color: var(--yellow);
            font-size: 1rem;
            font-weight: 700;
            text-align: center;
            padding: 1rem;
        }
        .enemy-sprite { color: var(--red); }
        .hero-sprite { color: var(--green); }
        .hud {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            align-items: center;
            color: var(--paper);
            margin-bottom: 0.25rem;
        }
        .hud-chip {
            padding: 0.28rem 0.52rem;
            background: #000;
            border: 2px solid var(--paper);
            color: var(--paper);
            font-size: 0.82rem;
        }
        .battle-name { color: var(--paper); font-size: 1.1rem; font-weight: 700; }
        .battle-role { color: var(--blue); font-size: 0.84rem; }
        .hp-track { height: 12px; background: #05070a; border: 2px solid var(--paper); margin-top: 0.35rem; }
        .hp-fill { height: 100%; background: var(--green); width: 82%; }
        .enemy-hp .hp-fill { background: var(--red); width: 76%; }
        .dialogue { color: var(--paper); line-height: 1.75; font-size: 1.04rem; }
        .danger-note { color: var(--yellow); font-size: 0.84rem; margin: 0.35rem 0 0.7rem; }
        div.stButton > button {
            border-radius: 0 !important;
            border: 3px solid var(--paper) !important;
            box-shadow: 4px 4px 0 #000 !important;
            background: var(--panel-2) !important;
            color: var(--paper) !important;
            min-height: 3.2rem !important;
            white-space: normal !important;
            text-align: left !important;
            font-family: "Courier New", "Malgun Gothic", monospace !important;
        }
        div.stButton > button:hover:enabled { border-color: var(--yellow) !important; color: var(--yellow) !important; }
        div.stButton > button:disabled { opacity: 0.42; }
        div[data-testid="stMetric"] { border: 2px solid var(--paper); background: var(--panel); padding: 0.55rem; }
        div[data-testid="stMetricValue"] { color: var(--yellow); }
        .feedback-good { color: var(--green); font-weight: 700; }
        .feedback-risk { color: var(--red); font-weight: 700; }
        .small-muted { color: #c5cbd4; font-size: 0.88rem; }
        @media (max-width: 680px) {
            .block-container { padding: 1rem 0.85rem 2rem; }
            .tower-frame { min-height: 180px; }
            .sprite-placeholder { min-height: 105px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    defaults = {
        "page": "landing",
        "player": {},
        "floor_index": 0,
        "scene_index": 0,
        "selections": [],
        "main_score": 0,
        "main_started_at": None,
        "main_seconds": None,
        "risk_used": False,
        "risk_success": False,
        "show_floor_feedback": False,
        "bonus_score": 0,
        "bonus_streak": 0,
        "bonus_attempts": 0,
        "bonus_result": None,
        "record_code": None,
        "submission_status": None,
        "submission_message": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_game() -> None:
    game_keys = [
        "page",
        "player",
        "floor_index",
        "scene_index",
        "selections",
        "main_score",
        "main_started_at",
        "main_seconds",
        "risk_used",
        "risk_success",
        "show_floor_feedback",
        "bonus_score",
        "bonus_streak",
        "bonus_attempts",
        "bonus_result",
        "record_code",
        "submission_status",
        "submission_message",
        "player_name",
        "player_department",
    ]
    for key in game_keys:
        st.session_state.pop(key, None)
    init_state()


def seconds_text(seconds: int | None) -> str:
    if seconds is None:
        return "측정 전"
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes:02d}:{remainder:02d}"


def render_sprite(filename: str, label: str, role: str) -> None:
    image_path = ASSET_DIR / filename
    if image_path.exists():
        st.image(str(image_path), width="stretch")
        return
    safe_label = html.escape(label)
    st.markdown(
        f'<div class="sprite-placeholder {role}-sprite">{safe_label}<br>SPRITE SLOT</div>',
        unsafe_allow_html=True,
    )


def render_tower() -> None:
    image_path = ASSET_DIR / "tower_intro.png"
    if image_path.exists():
        st.image(str(image_path), width="stretch")
        return
    st.markdown('<div class="tower-frame">담합의 탑<br>5F BATTLE QUEST</div>', unsafe_allow_html=True)


def current_elapsed() -> int:
    started_at = st.session_state.main_started_at
    if not started_at:
        return 0
    return max(0, int(time.time() - started_at))


def render_hud(floor_number: int, scene_number: int) -> None:
    st.markdown(
        "<div class='hud'>"
        f"<span class='hud-chip'>FLOOR {floor_number}/5</span>"
        f"<span class='hud-chip'>장면 {scene_number}/3</span>"
        f"<span class='hud-chip'>시간 {seconds_text(current_elapsed())}</span>"
        f"<span class='hud-chip'>위험 선택 {'사용함' if st.session_state.risk_used else '1회 가능'}</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_battle(floor: dict) -> None:
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("<div class='battle-name'>플레이어</div><div class='battle-role'>전략의 수호자</div>", unsafe_allow_html=True)
        st.markdown("<div class='hp-track'><div class='hp-fill'></div></div>", unsafe_allow_html=True)
        render_sprite("hero.png", "전략의 수호자", "hero")
    with right:
        st.markdown(
            f"<div class='battle-name'>{html.escape(floor['enemy'])}</div><div class='battle-role'>{html.escape(floor['team'])} 구역</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='hp-track enemy-hp'><div class='hp-fill'></div></div>", unsafe_allow_html=True)
        render_sprite(floor["asset"], floor["enemy"], "enemy")


def choose_main_option(floor: dict, scene: dict, option: dict) -> None:
    awarded_score = option["score"]
    risk_success = None
    feedback = option["feedback"]

    if option["kind"] == "risk":
        st.session_state.risk_used = True
        risk_success = random.randrange(100) < option["chance"]
        st.session_state.risk_success = risk_success
        if risk_success:
            awarded_score = option["reward"]
            feedback = (
                f"기적처럼 이번에는 감시망을 피했습니다. +{awarded_score}점. "
                "하지만 결과가 좋았다고 선택이 정당화되지는 않습니다. 실제 업무에서는 절대 기대면 안 되는 길입니다."
            )
        else:
            awarded_score = 0
            feedback = option["worst"]

    st.session_state.selections.append(
        {
            "floor": floor["number"],
            "scene": scene["title"],
            "choice_key": option["key"],
            "choice_text": option["text"],
            "kind": option["kind"],
            "score": awarded_score,
            "risk_success": risk_success,
            "feedback": feedback,
            "best": scene["best"],
        }
    )
    st.session_state.main_score += awarded_score

    if st.session_state.scene_index == len(floor["scenes"]) - 1:
        if st.session_state.floor_index == len(FLOORS) - 1:
            st.session_state.main_seconds = current_elapsed()
        st.session_state.show_floor_feedback = True
    else:
        st.session_state.scene_index += 1
    st.rerun()


def render_floor_feedback() -> None:
    floor = FLOORS[st.session_state.floor_index]
    results = [result for result in st.session_state.selections if result["floor"] == floor["number"]]
    floor_score = sum(result["score"] for result in results)

    st.title(f"{floor['number']}층 결산")
    st.markdown(f"<div class='pixel-panel'><p class='dialogue'>{html.escape(floor['closing'])}</p></div>", unsafe_allow_html=True)
    metrics = st.columns(3)
    metrics[0].metric("이번 층 점수", f"{floor_score}점")
    metrics[1].metric("누적 점수", f"{st.session_state.main_score}점")
    metrics[2].metric("선택 장면", f"{len(results)}개")

    for index, result in enumerate(results, start=1):
        risk_class = "feedback-risk" if result["kind"] == "risk" and not result["risk_success"] else "feedback-good"
        st.markdown(
            f"<div class='pixel-panel'><div class='{risk_class}'>{index}. {html.escape(result['scene'])} · {result['score']}점</div>"
            f"<p class='dialogue'>{html.escape(result['feedback'])}</p>"
            f"<p class='small-muted'>가장 안전한 대응: {html.escape(result['best'])}</p></div>",
            unsafe_allow_html=True,
        )

    if st.session_state.floor_index == len(FLOORS) - 1:
        button_label = "본편 결과 확인"
    else:
        button_label = f"{floor['number'] + 1}층으로 이동"

    if st.button(button_label, width="stretch", key="next_floor"):
        st.session_state.show_floor_feedback = False
        if st.session_state.floor_index == len(FLOORS) - 1:
            st.session_state.page = "main_result"
        else:
            st.session_state.floor_index += 1
            st.session_state.scene_index = 0
        st.rerun()


def render_main_game() -> None:
    if st.session_state.show_floor_feedback:
        render_floor_feedback()
        return

    floor = FLOORS[st.session_state.floor_index]
    scene = floor["scenes"][st.session_state.scene_index]
    render_hud(floor["number"], st.session_state.scene_index + 1)
    st.progress((st.session_state.floor_index * 3 + st.session_state.scene_index) / TOTAL_SCENES)
    st.title(f"{floor['number']}층 · {floor['title']}")
    st.caption(floor["opening"])
    render_battle(floor)
    st.markdown(
        f"<div class='pixel-panel'><h3>{html.escape(scene['title'])}</h3>"
        f"<p class='dialogue'>{html.escape(scene['situation'])}</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<p class='danger-note'>선택지의 일반 점수는 공개되지 않습니다. 본편의 위험 선택은 단 한 번만 사용할 수 있습니다.</p>", unsafe_allow_html=True)

    for option in scene["choices"]:
        is_risk = option["kind"] == "risk"
        disabled = is_risk and st.session_state.risk_used
        label = option["text"]
        if is_risk:
            suffix = "이미 사용함" if disabled else f"위험 선택 · 성공 확률 {option['chance']}% · 성공 시 +{option['reward']}점"
            label = f"{label}\n[{suffix}]"
        if st.button(
            label,
            key=f"choice_{floor['number']}_{st.session_state.scene_index}_{option['key']}",
            width="stretch",
            disabled=disabled,
        ):
            choose_main_option(floor, scene, option)


def main_title_and_feedback() -> tuple[str, list[str]]:
    score = st.session_state.main_score
    ordinary = [result for result in st.session_state.selections if result["kind"] == "normal"]
    score_100 = sum(result["score"] == 100 for result in ordinary)
    score_60 = sum(result["score"] == 60 for result in ordinary)
    score_40 = sum(result["score"] == 40 for result in ordinary)
    notes: list[str] = []

    if score >= 1350:
        title = "공정거래 수호자"
        notes.append("가격·물량·고객·입찰 조건의 위험 신호를 빠르게 구분했고, 거절 이후의 기록과 보고까지 연결했습니다.")
    elif score >= 1100:
        title = "원칙 설계자"
        notes.append("핵심 원칙은 지켰습니다. 이제는 모호한 접촉도 기록하고 공식 상담으로 연결하는 습관을 더해 보세요.")
    elif score >= 800:
        title = "경계선 감지자"
        notes.append("명백한 위험은 피했지만, 대화 이탈·증거 보존·보고 중 일부가 빠졌습니다.")
    else:
        title = "회색지대 탐험가"
        notes.append("성과 압박이나 관계 관리의 언어가 나와도 경쟁 민감정보의 교환과 활용은 선을 그어야 합니다.")

    if score_60:
        notes.append("거절만 하고 기록·보고를 생략한 선택이 있었습니다. 사후 대응까지 완료해야 조직이 위험을 관리할 수 있습니다.")
    if score_40:
        notes.append("상대의 말을 듣거나 우회 경로를 찾는 선택이 있었습니다. 숫자를 직접 말하지 않아도 민감정보의 취득·신호 교환은 위험합니다.")
    if st.session_state.risk_used and st.session_state.risk_success:
        notes.append("위험 선택은 운 좋게 통과했지만, 이 기록은 보너스일 뿐 실제 업무에서 허용되는 판단은 아닙니다.")
    if st.session_state.risk_used and not st.session_state.risk_success:
        notes.append("위험 선택이 실패했습니다. 가장 빠른 길처럼 보여도 조사·제재·신뢰 손상으로 이어질 수 있습니다.")
    if score_100 >= 10:
        notes.append("특히 독립적 의사결정의 원칙과 대체 가능한 업무 경로를 함께 제시한 점이 강점입니다.")
    return title, notes


def render_main_result() -> None:
    title, notes = main_title_and_feedback()
    st.title("본편 돌파 결과")
    st.markdown(
        f"<div class='pixel-panel'><h2>{html.escape(title)}</h2>"
        "<p class='dialogue'>담합의 탑 본편을 돌파했습니다. 점수만큼 중요한 것은, 실제 상황에서 위험한 대화의 경계를 인식하고 중단·기록·보고까지 실행하는 것입니다.</p></div>",
        unsafe_allow_html=True,
    )
    metrics = st.columns(3)
    metrics[0].metric("본편 점수", f"{st.session_state.main_score}점")
    metrics[1].metric("본편 시간", seconds_text(st.session_state.main_seconds))
    metrics[2].metric("위험 선택", "성공" if st.session_state.risk_success else "미사용" if not st.session_state.risk_used else "실패")

    for note in notes:
        st.markdown(f"<div class='pixel-panel'><p class='dialogue'>{html.escape(note)}</p></div>", unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        if st.button("마왕에게 도전한다", width="stretch", key="start_bonus"):
            st.session_state.page = "bonus"
            st.rerun()
    with right:
        if st.button("본편 기록 확정", width="stretch", key="finish_main"):
            st.session_state.page = "final"
            st.rerun()


def current_bonus_challenge() -> tuple[dict, int, int]:
    attempts = st.session_state.bonus_attempts
    challenge = BOSS_CHALLENGES[attempts % len(BOSS_CHALLENGES)]
    round_number = attempts // len(BOSS_CHALLENGES) + 1
    reward = challenge["reward"] + (round_number - 1) * 50
    return challenge, round_number, reward


def choose_bonus_challenge() -> None:
    challenge, round_number, reward = current_bonus_challenge()
    success = random.randrange(100) < 10
    st.session_state.bonus_attempts += 1
    if success:
        st.session_state.bonus_streak += 1
        st.session_state.bonus_score += reward
        st.session_state.bonus_result = {
            "success": True,
            "title": challenge["title"],
            "message": f"기적 발생. {reward}점 획득. 하지만 이 선택은 현실에서 가장 피해야 할 선택입니다.",
            "round": round_number,
        }
    else:
        st.session_state.bonus_result = {
            "success": False,
            "title": challenge["title"],
            "message": challenge["worst"],
            "round": round_number,
        }
    st.session_state.page = "bonus_outcome"
    st.rerun()


def render_bonus() -> None:
    challenge, round_number, reward = current_bonus_challenge()
    st.title("번외 · 마왕에게 도전")
    st.markdown(
        "<div class='pixel-panel'><p class='dialogue'>"
        "여기는 점수 경쟁을 위한 번외 구역입니다. 실제 업무에서 절대 선택하면 안 되는 길만 고릅니다. "
        "성공 확률은 매번 10%이며, 실패하면 그 선택의 최악의 결과를 확인하고 종료합니다."
        "</p></div>",
        unsafe_allow_html=True,
    )
    metrics = st.columns(3)
    metrics[0].metric("번외 점수", f"{st.session_state.bonus_score}점")
    metrics[1].metric("연속 통과", f"{st.session_state.bonus_streak}회")
    metrics[2].metric("심연 회차", f"{round_number}회차")
    render_battle(FLOORS[-1])
    st.markdown(
        f"<div class='pixel-panel'><h3>{html.escape(challenge['title'])}</h3>"
        f"<p class='dialogue'>{html.escape(challenge['situation'])}</p>"
        f"<p class='feedback-risk'>성공 확률 10% · 성공 시 +{reward}점</p></div>",
        unsafe_allow_html=True,
    )
    if st.button(challenge["action"], width="stretch", key="take_bonus_risk"):
        choose_bonus_challenge()
    if st.button("여기서 물러나고 기록 확정", width="stretch", key="end_bonus"):
        st.session_state.page = "final"
        st.rerun()


def render_bonus_outcome() -> None:
    outcome = st.session_state.bonus_result
    if not outcome:
        st.session_state.page = "bonus"
        st.rerun()
        return
    st.title("마왕의 판정")
    style = "feedback-good" if outcome["success"] else "feedback-risk"
    headline = "통과" if outcome["success"] else "패배"
    st.markdown(
        f"<div class='pixel-panel'><h2 class='{style}'>{headline}</h2>"
        f"<p class='dialogue'>{html.escape(outcome['message'])}</p></div>",
        unsafe_allow_html=True,
    )
    metrics = st.columns(2)
    metrics[0].metric("번외 점수", f"{st.session_state.bonus_score}점")
    metrics[1].metric("연속 통과", f"{st.session_state.bonus_streak}회")

    if outcome["success"]:
        left, right = st.columns(2)
        with left:
            if st.button("더 깊이 내려간다", width="stretch", key="continue_bonus"):
                st.session_state.page = "bonus"
                st.rerun()
        with right:
            if st.button("번외 기록 확정", width="stretch", key="finish_after_success"):
                st.session_state.page = "final"
                st.rerun()
    elif st.button("기록 확정", width="stretch", key="finish_after_failure"):
        st.session_state.page = "final"
        st.rerun()


def build_result_payload() -> dict:
    if not st.session_state.record_code:
        st.session_state.record_code = f"TOWER-{uuid.uuid4().hex[:8].upper()}"
    choices = " | ".join(
        f"{result['floor']}층-{result['scene']}:{result['score']}점" for result in st.session_state.selections
    )
    return {
        "record_code": st.session_state.record_code,
        "name": st.session_state.player["name"],
        "department": st.session_state.player["department"],
        "main_score": st.session_state.main_score,
        "main_seconds": st.session_state.main_seconds or 0,
        "bonus_score": st.session_state.bonus_score,
        "bonus_streak": st.session_state.bonus_streak,
        "bonus_attempts": st.session_state.bonus_attempts,
        "main_risk_used": "Y" if st.session_state.risk_used else "N",
        "main_risk_success": "Y" if st.session_state.risk_success else "N",
        "main_choices": choices,
    }


def render_final() -> None:
    payload = build_result_payload()
    st.title("기록의 방")
    st.markdown(
        f"<div class='pixel-panel'><h2>{html.escape(st.session_state.player['name'])} 님의 원정 기록</h2>"
        "<p class='dialogue'>본편 순위는 본편 점수 우선, 동점 시 플레이 시간 순으로 확인합니다. 번외는 번외 점수와 연속 통과 기록으로 별도 집계합니다.</p></div>",
        unsafe_allow_html=True,
    )
    metrics = st.columns(4)
    metrics[0].metric("본편", f"{payload['main_score']}점")
    metrics[1].metric("시간", seconds_text(payload["main_seconds"]))
    metrics[2].metric("번외", f"{payload['bonus_score']}점")
    metrics[3].metric("연속 통과", f"{payload['bonus_streak']}회")
    st.caption(f"기록 코드: {payload['record_code']}")

    if st.session_state.submission_status is True:
        st.success(st.session_state.submission_message)
    else:
        if st.session_state.submission_status is False:
            st.error(st.session_state.submission_message)
        if st.button("Google Sheets에 기록하기", width="stretch", key="submit_result"):
            try:
                success, message = append_result(st.secrets, payload)
            except Exception:
                success, message = False, "Google Sheets 시크릿이 아직 설정되지 않았습니다. README의 설정 예시를 확인해 주세요."
            st.session_state.submission_status = success
            st.session_state.submission_message = message
            st.rerun()

    if st.button("새 도전자 시작", width="stretch", key="new_game"):
        reset_game()
        st.rerun()


def render_landing() -> None:
    render_tower()
    st.caption("전략기획 · 전략투자 · 브랜드성장 컴플라이언스 배틀")
    st.markdown(
        "<div class='pixel-panel'><p class='dialogue'>"
        "5개 층, 15개의 실제 업무형 장면. 점수보다 먼저, 위험한 신호를 멈추고 기록하며 보고하는 판단을 시험합니다. "
        "본편의 위험 선택은 단 한 번뿐입니다."
        "</p></div>",
        unsafe_allow_html=True,
    )
    name = st.text_input("이름", max_chars=30, key="player_name", placeholder="이름을 입력하세요")
    department = st.selectbox("부서", DEPARTMENTS, key="player_department")
    if st.button("탑에 입장", width="stretch", key="start_game"):
        clean_name = name.strip()
        if not clean_name:
            st.warning("이름을 입력해 주세요.")
        else:
            st.session_state.player = {"name": clean_name, "department": department}
            st.session_state.main_started_at = time.time()
            st.session_state.page = "main_game"
            st.rerun()


def main() -> None:
    apply_style()
    init_state()
    page = st.session_state.page
    if page == "landing":
        render_landing()
    elif page == "main_game":
        render_main_game()
    elif page == "main_result":
        render_main_result()
    elif page == "bonus":
        render_bonus()
    elif page == "bonus_outcome":
        render_bonus_outcome()
    elif page == "final":
        render_final()
    else:
        reset_game()
        st.rerun()


if __name__ == "__main__":
    main()
