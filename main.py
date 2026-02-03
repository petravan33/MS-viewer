import sys
import pandas as pd
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QPushButton,
    QVBoxLayout,
    QWidget
)

class SpectrumViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MS Spectrum Viewer")
        self.resize(900, 600)

        self.plot = pg.PlotWidget(title="Mass Spectrum")
        self.plot.setBackground("w")
        self.plot.getAxis("left").setPen("k")
        self.plot.getAxis("bottom").setPen("k")
        self.plot.getAxis("left").setTextPen("k")
        self.plot.getAxis("bottom").setTextPen("k")
        self.plot.setLabel("bottom", "m/z")
        self.plot.setLabel("left", "Intensity")
        self.plot.showGrid(x=True, y=True)

        self.plot.setLimits(
            xMin=0,
            yMin=0
        )

        self.plot.setXRange(0, 500, padding=0)
        self.plot.setYRange(0, 105, padding=0)

        self.load_button = QPushButton("Open CSV")
        self.load_button.clicked.connect(self.load_csv)

        layout = QVBoxLayout()
        layout.addWidget(self.load_button)
        layout.addWidget(self.plot)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.plot.sigXRangeChanged.connect(self.update_annotations)
        self.annotations = []

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        df = pd.read_csv(file_path, sep="\t", encoding="utf-16")

        x = df["m/z"].values
        y = df["intensity"].values

        self.plot.clear()

        for mz, intensity in zip(x, y):
            self.plot.plot(
                [mz, mz],
                [0, intensity],
                pen=pg.mkPen("k", width=1)
            )
        y = y / y.max() * 100
        self.plot.setYRange(0, 105)
        self.plot.setMouseEnabled(x=True, y=False)
        self.plot.setLabel("left", "Intensity (%)")

        # annotate strongest peaks
        top_peaks = df.nlargest(5, "intensity")
        for _, row in top_peaks.iterrows():
            label = pg.TextItem(
                text=f"{row['m/z']:.2f}",
                anchor=(0.5, 1),
                color="red"
            )
            self.plot.addItem(label)
            label.setPos(row["m/z"], row["intensity"])
        self.df = df
        self.x = x
        self.y = y
        self.update_annotations()
        self.plot.setXRange(0, self.x.max() * 1.02, padding=0)

    def update_annotations(self):
        # remove old labels
        for label in self.annotations:
            self.plot.removeItem(label)
        self.annotations.clear()

        if not hasattr(self, "df"):
            return

        xmin, xmax = self.plot.viewRange()[0]

        visible = self.df[
            (self.df["m/z"] >= xmin) &
            (self.df["m/z"] <= xmax)
        ]

        if visible.empty:
            return

        # label strongest peaks in view
        peaks = visible.nlargest(5, "intensity")

        ymax = self.y.max()

        for _, row in peaks.iterrows():
            label = pg.TextItem(
                text=f"{row['m/z']:.4f}",
                anchor=(0.5, 1),
                color="k"
            )
            self.plot.addItem(label)
            label.setPos(
            row["m/z"],
            (row["intensity"] / ymax) * 105
            )
            self.annotations.append(label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SpectrumViewer()
    viewer.show()
    sys.exit(app.exec())
