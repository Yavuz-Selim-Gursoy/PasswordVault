import os
import sys

from PySide6.QtWidgets import QApplication

from gui_assets.main_window import MainWindow


def main():
    # Qt uygulaması oluştur
    app = QApplication(sys.argv)
    app.setApplicationName("Parola Kasası")
    app.setApplicationVersion("1.0.0")

    # Vault dizinini oluştur
    vaults_dir = os.path.join(os.path.dirname(__file__), "vaults")
    os.makedirs(vaults_dir, exist_ok=True)

    # Ana pencereyi göster
    window = MainWindow()
    window.show()

    # Uygulamayı çalıştır
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
