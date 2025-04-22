import sys
import os
import json
import anthropic
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, 
                            QTabWidget, QHBoxLayout, QMessageBox, QFormLayout,
                            QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette

# API 키 설정 - 실제 사용 시에는 환경 변수나 설정 파일에서 불러오는 것이 좋습니다
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"
AI_MODEL = "claude-3-7-sonnet-20250219"  # Claude 3.7 Sonnet 모델

# 프로그램 설정 및 프롬프트 기본값
DEFAULT_SETTINGS = {
    "saju_prompt": """
    1. 사주팔자 기본 분석 (오행, 십이지, 사주의 특징)
    2. {current_year}년의 운세 (현재 연도에 대한 구체적인 분석)
    3. 건강, 금전, 사랑 관련 운세
    4. 주의해야 할 점과 길운을 부를 수 있는 조언
    """,
    "counsel_prompt": """
    1. 사용자의 사주팔자와 현재({current_year}년) 운세를 고려하여 고민에 대한 통찰력 있는 답변을 제공하세요
    2. 계절과 절기를 고려한 시기적 조언을 포함하세요
    3. 문제 해결을 위한 구체적인 조언을 제시하세요
    4. 긍정적인 에너지와 희망을 주는 메시지를 포함하세요
    5. 필요하다면 기도, 부적, 의식 등의 무속적 조언을 제공하세요
    6. 재회굿은 한국 전통에는 없으니 안내하지 말고, 사기를 조심하라고 하세요
    """
}

# 전역 스타일 정의
GLOBAL_STYLE = """
QMainWindow, QWidget {
    background-color: #2D2D30;
    color: #E0E0E0;
}

QLabel {
    color: #E0E0E0;
}

QLineEdit, QTextEdit {
    background-color: #1E1E1E;
    color: #E0E0E0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px;
    selection-background-color: #8E2DC5;
}

QTabWidget::pane {
    border: 1px solid #3E3E42;
    background-color: #2D2D30;
}

QTabBar::tab {
    background-color: #3E3E42;
    color: #E0E0E0;
    padding: 8px 12px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #8E2DC5;
    color: white;
}

QPushButton {
    background-color: #444444;
    color: #E0E0E0;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #555555;
}

QPushButton:pressed {
    background-color: #666666;
}

QRadioButton {
    color: #E0E0E0;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QRadioButton::indicator:checked {
    background-color: #8E2DC5;
    border: 2px solid #E0E0E0;
    border-radius: 8px;
}

QRadioButton::indicator:unchecked {
    background-color: #1E1E1E;
    border: 2px solid #555555;
    border-radius: 8px;
}
"""

class MudangGPT(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = DEFAULT_SETTINGS.copy()
        self.init_ui()
        self.client = None
        self.try_connect_api()
        
    def try_connect_api(self):
        try:
            if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "YOUR_ANTHROPIC_API_KEY":
                self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                self.status_label.setText("API 연결 성공")
                self.status_label.setStyleSheet("color: #50C878;")  # 성공 시 초록색
            else:
                self.status_label.setText("API 키를 설정해주세요")
                self.status_label.setStyleSheet("color: #FFA500;")  # 경고 시 주황색
        except Exception as e:
            self.status_label.setText(f"API 연결 실패: {str(e)}")
            self.status_label.setStyleSheet("color: #FF6347;")  # 오류 시 빨간색
            
    def init_ui(self):
        self.setWindowTitle('무당 GPT - 사주팔자 & 고민상담')
        self.setGeometry(100, 100, 800, 600)
        
        # 스타일 적용
        self.setStyleSheet(GLOBAL_STYLE)
        
        # 메인 위젯과 레이아웃
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)  # 여백 추가
        main_layout.setSpacing(10)  # 위젯 간 간격
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # 상단 정보 입력 부분
        info_widget = QWidget()
        info_layout = QFormLayout()
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(10)
        
        # 이름 입력 필드
        name_label = QLabel("이름 (한자)")
        name_label.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("예: 홍길동(洪吉東)")
        self.name_input.setMinimumHeight(30)
        self.name_input.setFont(QFont("Malgun Gothic", 11))
        info_layout.addRow(name_label, self.name_input)
        
        # 생년월일 입력 필드
        birth_label = QLabel("생년월일")
        birth_label.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
        self.birthdate_input = QLineEdit()
        self.birthdate_input.setPlaceholderText("예: 2002.04.27")
        self.birthdate_input.setMinimumHeight(30)
        self.birthdate_input.setFont(QFont("Malgun Gothic", 11))
        info_layout.addRow(birth_label, self.birthdate_input)
        
        # 태어난 시간 필드
        time_label = QLabel("태어난 시간")
        time_label.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("예: 14:30 (24시간제)")
        self.time_input.setMinimumHeight(30)
        self.time_input.setFont(QFont("Malgun Gothic", 11))
        info_layout.addRow(time_label, self.time_input)
        
        # 성별 선택 필드
        gender_label = QLabel("성별")
        gender_label.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
        
        gender_widget = QWidget()
        gender_layout = QHBoxLayout()
        gender_layout.setContentsMargins(0, 0, 0, 0)
        gender_layout.setSpacing(15)
        
        self.gender_group = QButtonGroup(self)
        
        self.male_radio = QRadioButton("남성")
        self.male_radio.setFont(QFont("Malgun Gothic", 11))
        self.male_radio.setChecked(True)  # 기본값 설정
        self.gender_group.addButton(self.male_radio, 1)
        gender_layout.addWidget(self.male_radio)
        
        self.female_radio = QRadioButton("여성")
        self.female_radio.setFont(QFont("Malgun Gothic", 11))
        self.gender_group.addButton(self.female_radio, 2)
        gender_layout.addWidget(self.female_radio)
        
        gender_layout.addStretch()
        gender_widget.setLayout(gender_layout)
        
        info_layout.addRow(gender_label, gender_widget)
        
        info_widget.setLayout(info_layout)
        main_layout.addWidget(info_widget)
        
        # 탭 위젯 설정
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
        
        # 사주팔자 탭
        self.saju_tab = QWidget()
        saju_layout = QVBoxLayout()
        saju_layout.setContentsMargins(10, 15, 10, 10)
        saju_layout.setSpacing(15)
        
        # 사주팔자 버튼
        self.saju_button = QPushButton("사주팔자 보기")
        self.saju_button.setMinimumHeight(45)
        self.saju_button.setFont(QFont("Malgun Gothic", 12, QFont.Bold))
        self.saju_button.setStyleSheet("""
            QPushButton {
                background-color: #8E2DC5;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #9D3DD4;
            }
            QPushButton:pressed {
                background-color: #7D1DB5;
            }
        """)
        self.saju_button.clicked.connect(self.analyze_saju)
        saju_layout.addWidget(self.saju_button)
        
        # 사주팔자 결과 표시
        self.saju_result = QTextEdit()
        self.saju_result.setReadOnly(True)
        self.saju_result.setFont(QFont("Malgun Gothic", 11))
        self.saju_result.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        saju_layout.addWidget(self.saju_result)
        
        self.saju_tab.setLayout(saju_layout)
        self.tabs.addTab(self.saju_tab, "사주팔자")
        
        # 고민상담 탭
        self.counsel_tab = QWidget()
        counsel_layout = QVBoxLayout()
        counsel_layout.setContentsMargins(10, 15, 10, 10)
        counsel_layout.setSpacing(15)
        
        # 고민 입력 레이블
        worry_label = QLabel("고민을 입력해주세요:")
        worry_label.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
        counsel_layout.addWidget(worry_label)
        
        # 고민 입력 필드
        self.worry_input = QTextEdit()
        self.worry_input.setPlaceholderText("당신의 고민을 자세히 적어주세요...")
        self.worry_input.setFont(QFont("Malgun Gothic", 11))
        self.worry_input.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.worry_input.setMinimumHeight(100)
        counsel_layout.addWidget(self.worry_input)
        
        # 상담 버튼
        self.counsel_button = QPushButton("상담 받기")
        self.counsel_button.setMinimumHeight(45)
        self.counsel_button.setFont(QFont("Malgun Gothic", 12, QFont.Bold))
        self.counsel_button.setStyleSheet("""
            QPushButton {
                background-color: #8E2DC5;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #9D3DD4;
            }
            QPushButton:pressed {
                background-color: #7D1DB5;
            }
        """)
        self.counsel_button.clicked.connect(self.get_counsel)
        counsel_layout.addWidget(self.counsel_button)
        
        # 상담 결과 표시
        self.counsel_result = QTextEdit()
        self.counsel_result.setReadOnly(True)
        self.counsel_result.setFont(QFont("Malgun Gothic", 11))
        self.counsel_result.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        counsel_layout.addWidget(self.counsel_result)
        
        self.counsel_tab.setLayout(counsel_layout)
        self.tabs.addTab(self.counsel_tab, "고민상담")
        
        main_layout.addWidget(self.tabs)
        
        # 하단 버튼 영역
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        
        # 프롬프트 편집 버튼
        self.prompt_edit_button = QPushButton("프롬프트 편집")
        self.prompt_edit_button.setFont(QFont("Malgun Gothic", 10))
        self.prompt_edit_button.setMinimumHeight(35)
        self.prompt_edit_button.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                color: #E0E0E0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
            }
        """)
        self.prompt_edit_button.clicked.connect(self.open_prompt_editor)
        bottom_layout.addWidget(self.prompt_edit_button)
        
        bottom_layout.addStretch()
        
        # 상태 표시줄
        self.status_label = QLabel("API 연결 대기 중...")
        self.status_label.setFont(QFont("Malgun Gothic", 9))
        bottom_layout.addWidget(self.status_label)
        
        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_layout)
        main_layout.addWidget(bottom_widget)
    
    def get_gender(self):
        """선택된 성별 반환"""
        return "남성" if self.male_radio.isChecked() else "여성"
    
    def validate_inputs(self):
        name = self.name_input.text().strip()
        birthdate = self.birthdate_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "입력 오류", "이름을 입력해주세요.")
            return False
        
        # 생년월일 형식 검증 (YYYY.MM.DD)
        try:
            datetime.strptime(birthdate, "%Y.%m.%d")
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "생년월일 형식이 올바르지 않습니다. YYYY.MM.DD 형식으로 입력해주세요.")
            return False
            
        return True
    
    def analyze_saju(self):
        if not self.validate_inputs() or not self.client:
            return
            
        self.saju_result.setText("사주팔자 분석 중...")
        QApplication.processEvents()
        
        name = self.name_input.text().strip()
        birthdate = self.birthdate_input.text().strip()
        birthtime = self.time_input.text().strip()
        gender = self.get_gender()
        
        # 현재 연도 가져오기
        current_year = datetime.now().year
        
        try:
            # 설정에서 사주 프롬프트 가져오기 (현재 연도 포맷 적용)
            saju_content = self.settings["saju_prompt"].format(current_year=current_year)
            
            prompt = f"""
            당신은 경험 많은 무당입니다. 사주팔자를 보는 전문가로서 사용자의 정보를 바탕으로 운세와 사주를 분석해주세요.
            
            ## 사용자 정보
            이름: {name}
            성별: {gender}
            생년월일: {birthdate}
            태어난 시간: {birthtime}
            
            ## 분석해야 할 내용
            {saju_content}
            
            ## 응답 형식
            - 무당(점쟁이)처럼 신비롭고 직관적인 언어를 사용하세요
			- 젊은 여성 무당처럼 친근하고 발랄한 언어를 사용하세요
			- "~이에요", "~네요", "~했어요" 같은 현대적인 말투를 사용하세요
			- 때로는 이모티콘이나 감탄사(와, 후, 음~)를 사용하여 친근감을 주세요
            - 한국 무당의 어투와 표현을 사용하세요
			- 시주(時柱)까지 포함한 완전한 사주팔자 분석을 제공하세요
            - 구체적인 사항들을 언급하세요
            - 관용적인 무속 표현을 적절히 사용하세요
            - 결과는 여러 파트로 나누어 각각 제목을 붙여주세요
            - 성별에 맞는 사주팔자 해석을 제공하세요
            """
            
            response = self.client.messages.create(
                model=AI_MODEL,
                max_tokens=2000,
                temperature=0.7,
                system="당신은 한국의 전통 무당입니다. 사주팔자와 운세를 보는 전문가로서 신비롭고 직관적인 언어를 사용합니다.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            self.saju_result.setText(response.content[0].text)
            
        except Exception as e:
            self.saju_result.setText(f"분석 중 오류가 발생했습니다: {str(e)}")
            self.status_label.setText(f"API 오류: {str(e)}")
            self.status_label.setStyleSheet("color: #FF6347;")  # 오류 시 빨간색
    
    def get_counsel(self):
        if not self.validate_inputs() or not self.client:
            return
            
        worry = self.worry_input.toPlainText().strip()
        if not worry:
            QMessageBox.warning(self, "입력 오류", "고민을 입력해주세요.")
            return
            
        self.counsel_result.setText("고민 상담 중...")
        QApplication.processEvents()
        
        name = self.name_input.text().strip()
        birthdate = self.birthdate_input.text().strip()
        gender = self.get_gender()
        birthtime = self.time_input.text().strip()
        
        # 현재 연도 가져오기
        current_year = datetime.now().year
        
        try:
            # 설정에서 상담 프롬프트 가져오기 (현재 연도 포맷 적용)
            counsel_content = self.settings["counsel_prompt"].format(current_year=current_year)
            
            prompt = f"""
            당신은 경험 많은 무당입니다. 사주팔자를 보며 상담을 해주는 전문가로서 사용자의 고민을 해결해주세요.
            
            ## 사용자 정보
            이름: {name}
            성별: {gender}
            생년월일: {birthdate}
            태어난 시간: {birthtime}
            현재 연도: {current_year}
            
            ## 사용자의 고민
            {worry}
            
            ## 상담 방향
            {counsel_content}
            
            ## 응답 형식
			- 젊은 여성 무당처럼 친근하고 발랄한 언어를 사용하세요
			- "~이에요", "~네요", "~했어요" 같은 현대적인 말투를 사용하세요
			- 공감과 이해를 바탕으로 한 따뜻한 조언을 제공하세요
			- 때로는 이모티콘이나 감탄사(와, 후, 음~)를 사용하여 친근감을 주세요
            - 무당(점쟁이)처럼 신비롭고 직관적인 언어를 사용하세요
            - 한국 무당의 어투와 표현을 사용하세요
            - 공감과 이해를 바탕으로 한 따뜻한 조언을 제공하세요
            - 너무 길지 않게 핵심적인 조언을 제공하세요
            - 성별을 고려한 맞춤형 조언을 제공하세요
            """
            
            response = self.client.messages.create(
                model=AI_MODEL,
                max_tokens=2000,
                temperature=0.7,
                system="당신은 한국의 전통 무당입니다. 사주팔자를 보며 고민 상담을 해주는 전문가로서 신비롭고 직관적인 언어를 사용합니다.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            self.counsel_result.setText(response.content[0].text)
            
        except Exception as e:
            self.counsel_result.setText(f"상담 중 오류가 발생했습니다: {str(e)}")
            self.status_label.setText(f"API 오류: {str(e)}")
            self.status_label.setStyleSheet("color: #FF6347;")  # 오류 시 빨간색
    
    def open_prompt_editor(self):
        # 프롬프트 편집기 창 열기
        self.editor = PromptEditor(self.settings, self)
        self.editor.show()


# 별도의 프롬프트 편집기 창
class PromptEditor(QMainWindow):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_settings = current_settings.copy()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('무당 GPT - 프롬프트 편집기')
        self.setGeometry(200, 200, 700, 500)
        
        # 전역 스타일 적용
        self.setStyleSheet(GLOBAL_STYLE)
        
        # 메인 위젯과 레이아웃
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # 탭 위젯 설정
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
        
        # 사주팔자 프롬프트 탭
        self.saju_tab = QWidget()
        saju_layout = QVBoxLayout()
        saju_layout.setContentsMargins(10, 15, 10, 10)
        saju_layout.setSpacing(10)
        
        # 제목과 안내
        title_label = QLabel("사주팔자 분석 프롬프트")
        title_label.setFont(QFont("Malgun Gothic", 12, QFont.Bold))
        saju_layout.addWidget(title_label)
        
        info_label = QLabel("{current_year}는 현재 연도로 자동 치환됩니다.")
        info_label.setFont(QFont("Malgun Gothic", 9))
        info_label.setStyleSheet("color: #AAAAAA;")
        saju_layout.addWidget(info_label)
        
        # 텍스트 에디터
        self.saju_prompt_edit = QTextEdit()
        self.saju_prompt_edit.setFont(QFont("Malgun Gothic", 11))
        self.saju_prompt_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.saju_prompt_edit.setPlainText(self.current_settings["saju_prompt"].strip())
        saju_layout.addWidget(self.saju_prompt_edit)
        
        self.saju_tab.setLayout(saju_layout)
        self.tabs.addTab(self.saju_tab, "사주팔자 프롬프트")
        
        # 고민상담 프롬프트 탭
        self.counsel_tab = QWidget()
        counsel_layout = QVBoxLayout()
        counsel_layout.setContentsMargins(10, 15, 10, 10)
        counsel_layout.setSpacing(10)
        
        # 제목과 안내
        title_label = QLabel("고민상담 프롬프트")
        title_label.setFont(QFont("Malgun Gothic", 12, QFont.Bold))
        counsel_layout.addWidget(title_label)
        
        info_label = QLabel("{current_year}는 현재 연도로 자동 치환됩니다.")
        info_label.setFont(QFont("Malgun Gothic", 9))
        info_label.setStyleSheet("color: #AAAAAA;")
        counsel_layout.addWidget(info_label)
        
        # 텍스트 에디터
        self.counsel_prompt_edit = QTextEdit()
        self.counsel_prompt_edit.setFont(QFont("Malgun Gothic", 11))
        self.counsel_prompt_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.counsel_prompt_edit.setPlainText(self.current_settings["counsel_prompt"].strip())
        counsel_layout.addWidget(self.counsel_prompt_edit)
        
        self.counsel_tab.setLayout(counsel_layout)
        self.tabs.addTab(self.counsel_tab, "고민상담 프롬프트")
        
        main_layout.addWidget(self.tabs)
        
        # 하단 버튼 영역
        bottom_layout = QHBoxLayout()
        
        # 초기화 버튼
        self.reset_button = QPushButton("기본값으로 초기화")
        self.reset_button.setFont(QFont("Malgun Gothic", 10))
        self.reset_button.setMinimumHeight(35)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                color: #E0E0E0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
            }
        """)
        self.reset_button.clicked.connect(self.reset_to_default)
        bottom_layout.addWidget(self.reset_button)
        
        bottom_layout.addStretch()
        
        # 취소 버튼
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setFont(QFont("Malgun Gothic", 10))
        self.cancel_button.setMinimumHeight(35)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                color: #E0E0E0;
                border-radius: 4px;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
            }
        """)
        self.cancel_button.clicked.connect(self.close)
        bottom_layout.addWidget(self.cancel_button)
        
        # 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
        self.save_button.setMinimumHeight(35)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #8E2DC5;
                color: white;
                border-radius: 4px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #9D3DD4;
            }
            QPushButton:pressed {
                background-color: #7D1DB5;
            }
        """)
        self.save_button.clicked.connect(self.save_settings)
        bottom_layout.addWidget(self.save_button)
        
        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_layout)
        main_layout.addWidget(bottom_widget)
    
    def reset_to_default(self):
        # 기본값으로 복원
        reply = QMessageBox.question(self, '초기화 확인', '프롬프트를 기본값으로 되돌리시겠습니까?',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.saju_prompt_edit.setPlainText(DEFAULT_SETTINGS["saju_prompt"].strip())
            self.counsel_prompt_edit.setPlainText(DEFAULT_SETTINGS["counsel_prompt"].strip())
		
    def save_settings(self):
        # 설정 저장
        self.current_settings["saju_prompt"] = self.saju_prompt_edit.toPlainText()
        self.current_settings["counsel_prompt"] = self.counsel_prompt_edit.toPlainText()
        
        if self.parent:
            self.parent.settings = self.current_settings.copy()
            QMessageBox.information(self, "저장 완료", "프롬프트가 성공적으로 저장되었습니다.")
        else:
            QMessageBox.warning(self, "저장 실패", "부모 창을 찾을 수 없습니다.")
        
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Fusion 스타일 적용하여 일관된 모양 유지
    window = MudangGPT()
    window.show()
    sys.exit(app.exec_())
