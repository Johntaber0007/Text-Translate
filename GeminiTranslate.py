from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QByteArray, Qt
import sys
import google.generativeai as genai

class TranslatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.api_key = ""
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Gemini Translate")
        self.setFixedSize(800, 600)

        self.set_window_icon()

        main_layout = QVBoxLayout()

        api_layout = QHBoxLayout()
        self.api_label = QLabel("API Key:")
        self.api_input = QLineEdit(self)
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.api_label)
        api_layout.addWidget(self.api_input)
        main_layout.addLayout(api_layout)

        model_layout = QHBoxLayout()
        self.model_label = QLabel("Model:")
        self.model_selector = QComboBox()
        self.model_selector.addItems([
            "gemini-2.0-flash-001",
            "gemini-2.0-flash-lite-preview-02-05",
            "gemini-1.5-pro-002",
            "gemini-1.5-flash-002",
            "gemini-1.5-flash-8b-001"
        ])
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_selector)
        main_layout.addLayout(model_layout)

        text_layout = QHBoxLayout()

        input_layout = QVBoxLayout()
        self.input_label = QLabel("Text:")
        self.input_text = QTextEdit(self)
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_text)

        output_layout = QVBoxLayout()
        self.output_label = QLabel("Result:")
        self.output_text = QTextEdit(self)
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_text)

        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_result_to_clipboard)
        output_layout.addWidget(self.copy_button)

        text_layout.addLayout(input_layout)
        text_layout.addLayout(output_layout)

        main_layout.addLayout(text_layout)

        self.translate_button = QPushButton("Translate")
        self.translate_button.clicked.connect(self.start_translation_text)
        main_layout.addWidget(self.translate_button)

        prompt_layout = QVBoxLayout()
        self.prompt_inputs = []
        self.prompt_group = QButtonGroup(self)

        for i in range(5):
            row_layout = QHBoxLayout()
            prompt_radio = QRadioButton()
            prompt_label = QLabel(f"Prompt {i+1}:")
            prompt_input = QLineEdit(self)
            self.prompt_group.addButton(prompt_radio, i)
            self.prompt_inputs.append((prompt_input, prompt_radio))
            row_layout.addWidget(prompt_radio)
            row_layout.addWidget(prompt_label)
            row_layout.addWidget(prompt_input)
            prompt_layout.addLayout(row_layout)
        
        self.prompt_inputs[0][1].setChecked(True)
        main_layout.addLayout(prompt_layout)

        temp_layout = QHBoxLayout()
        self.temp_label = QLabel("Temperature: 0.0")
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 10)
        self.temp_slider.setValue(0)
        self.temp_slider.valueChanged.connect(self.update_temperature_label)

        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_slider)
        main_layout.addLayout(temp_layout)

        self.status_display = QTextEdit(self)
        self.status_display.setReadOnly(True)
        self.status_display.setFixedHeight(100)
        main_layout.addWidget(self.status_display)

        self.setLayout(main_layout)

    def set_window_icon(self):
        base64_icon = """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"""  # Add your icon base64 data here
        image_data = QByteArray.fromBase64(base64_icon.encode())
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        self.setWindowIcon(QIcon(pixmap))

    def start_translation_text(self):
        self.api_key = self.api_input.text().strip()
        if not self.api_key:
            self.status_display.append("Please enter an API key!")
            return

        genai.configure(api_key=self.api_key)
        
        selected_prompt_index = self.prompt_group.checkedId()
        if selected_prompt_index == -1:
            self.status_display.append("Please select a prompt!")
            return
        
        prompt_text = self.prompt_inputs[selected_prompt_index][0].text().strip()
        if not prompt_text:
            self.status_display.append("Selected prompt is empty!")
            return
        
        text_to_translate = self.input_text.toPlainText().strip()
        if not text_to_translate:
            self.status_display.append("Please enter text to translate!")
            return

        self.status_display.append("Starting translation...")
        temperature = self.temp_slider.value() / 10.0
        model_name = self.model_selector.currentText()
        
        translated_text = self.gemini_translate(model_name, prompt_text, text_to_translate, temperature)
        self.output_text.setPlainText(translated_text)
        self.status_display.append("Translation complete!")

    def gemini_translate(self, model_name, prompt, text, temperature):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(f"{prompt}\n{text}", generation_config={"temperature": temperature})
            return response.text.strip().replace("\n", " ")
        except Exception as e:
            self.status_display.append(f"Error during translation: {str(e)}")
            return text

    def copy_result_to_clipboard(self):
        result_text = self.output_text.toPlainText()
        if result_text.strip():
            clipboard = QApplication.clipboard()
            clipboard.setText(result_text)
            self.status_display.append("Result copied to clipboard!")
        else:
            self.status_display.append("No text to copy!")

    def update_temperature_label(self):
        self.temp_label.setText(f"Temperature: {self.temp_slider.value() / 10.0}")


def main():
    app = QApplication(sys.argv)
    translator_app = TranslatorApp()
    translator_app.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
