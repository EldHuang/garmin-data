import os
import shutil
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator


class GarminGraphs:

    # ============================================================
    # COLORS — CHANGE THESE
    # ============================================================

    BACKGROUND = "#080A0F"
    PLOT_BACKGROUND = "#0D1117"
    TEXT = "#F2F4F7"
    TICKS = "#8A94A3"
    GRID = "#252B35"

    STEPS_COLOR = "#55E6A5"
    VO2_COLOR = "#A970FF"
    SLEEP_COLOR = "#58A6FF"
    STRESS_COLOR = "#FFD166"
    HEART_RESTING_COLOR = "#FF5C8A"
    HEART_MAX_COLOR = "#FF3B30"

    # ============================================================
    # GRAPH SETTINGS
    # ============================================================

    FIG_WIDTH = 19.2
    FIG_HEIGHT = 10.8
    DPI = 100

    TITLE_SIZE = 30
    AXIS_LABEL_SIZE = 20
    TICK_SIZE = 14
    LINE_WIDTH = 3.5
    MARKER_SIZE = 6
    EXTREME_LABEL_SIZE = 14
    NUMBER_SIZE = 58
    CAPTION_SIZE = 17
    GRID_ALPHA = 0.35
    GRID_WIDTH = 0.8

    BASE_OUTPUT_DIR = "./graphs"

    # ============================================================
    # INITIALIZE
    # ============================================================

    def __init__(self, data):
        self.data = data
        self.output_dir = None

    # ============================================================
    # OUTPUT FOLDER
    # ============================================================

    def setup_output_folder(self):
        month_year = datetime.now().strftime("%B_%Y")
        self.output_dir = os.path.join(self.BASE_OUTPUT_DIR, month_year)

        os.makedirs(self.BASE_OUTPUT_DIR, exist_ok=True)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"\nCreated output folder: {self.output_dir}")
            return True

        print()
        print("=" * 60)
        print(f'Folder "{month_year}" already exists.')
        print("This will delete everything inside that folder.")
        print("=" * 60)

        response = input(
            "Delete everything inside it and regenerate? [y/N]: "
        ).strip().lower()

        if response not in ("y", "yes"):
            print("\nCancelled. No files were changed.")
            return False

        print("\nDeleting existing files...")

        for filename in os.listdir(self.output_dir):
            path = os.path.join(self.output_dir, filename)

            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except OSError as error:
                print(f"Could not delete {path}: {error}")

        print("Folder cleared.")
        return True

    # ============================================================
    # FIGURE
    # ============================================================

    def create_figure(self):
        fig, ax = plt.subplots(
            figsize=(self.FIG_WIDTH, self.FIG_HEIGHT),
            dpi=self.DPI
        )

        fig.patch.set_facecolor(self.BACKGROUND)
        ax.set_facecolor(self.PLOT_BACKGROUND)

        return fig, ax

    # ============================================================
    # AXIS STYLE
    # ============================================================

    def style_axis(self, ax):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(self.GRID)
        ax.spines["bottom"].set_color(self.GRID)

        ax.grid(
            True,
            color=self.GRID,
            alpha=self.GRID_ALPHA,
            linewidth=self.GRID_WIDTH
        )

        ax.tick_params(
            length=0,
            pad=10,
            colors=self.TICKS,
            labelsize=self.TICK_SIZE
        )

        ax.xaxis.label.set_color(self.TEXT)
        ax.yaxis.label.set_color(self.TEXT)

        ax.xaxis.label.set_size(self.AXIS_LABEL_SIZE)
        ax.yaxis.label.set_size(self.AXIS_LABEL_SIZE)

    # ============================================================
    # SAVE GRAPH
    # ============================================================

    def save_graph(self, fig, filename):
        if self.output_dir is None:
            raise RuntimeError("Output folder has not been initialized.")

        os.makedirs(self.output_dir, exist_ok=True)

        path = os.path.join(self.output_dir, filename)

        fig.savefig(
            path,
            dpi=self.DPI,
            facecolor=self.BACKGROUND,
            edgecolor="none",
            bbox_inches="tight",
            pad_inches=0.25
        )

        plt.close(fig)

        print(f"Saved: {filename}")

    # ============================================================
    # DATE CONVERSION
    # ============================================================

    def convert_dates(self, dictionary):
        dates = []
        values = []

        for date_string, value in dictionary.items():
            if value is None:
                continue

            try:
                parsed = datetime.strptime(
                    date_string,
                    "%Y-%m-%d"
                )
            except (ValueError, TypeError):
                continue

            dates.append(parsed)
            values.append(value)

        return dates, values

    # ============================================================
    # DATE AXIS
    # ============================================================

    def date_axis(self, ax):
        locator = mdates.AutoDateLocator(
            minticks=6,
            maxticks=10
        )

        formatter = mdates.DateFormatter("%b %d")

        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        plt.setp(
            ax.get_xticklabels(),
            rotation=45,
            ha="right"
        )

    # ============================================================
    # LABEL HIGH / LOW
    # ============================================================

    def annotate_extremes(
        self,
        ax,
        dates,
        values,
        color,
        decimals=0
    ):
        if not dates or not values:
            return

        # HIGH
        high_index = values.index(max(values))
        high_date = dates[high_index]
        high_value = values[high_index]

        if decimals == 0:
            high_text = f"HIGH  {high_value:,.0f}"
        else:
            high_text = f"HIGH  {high_value:.{decimals}f}"

        ax.scatter(
            high_date,
            high_value,
            color=color,
            s=110,
            zorder=10,
            edgecolors=self.TEXT,
            linewidths=2
        )

        ax.annotate(
            high_text,
            xy=(high_date, high_value),
            xytext=(0, 28),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=self.EXTREME_LABEL_SIZE,
            fontweight="bold",
            color=self.TEXT
        )

        # LOW
        low_index = values.index(min(values))
        low_date = dates[low_index]
        low_value = values[low_index]

        if decimals == 0:
            low_text = f"LOW  {low_value:,.0f}"
        else:
            low_text = f"LOW  {low_value:.{decimals}f}"

        ax.scatter(
            low_date,
            low_value,
            color=color,
            s=110,
            zorder=10,
            edgecolors=self.TEXT,
            linewidths=2
        )

        ax.annotate(
            low_text,
            xy=(low_date, low_value),
            xytext=(0, -35),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=self.EXTREME_LABEL_SIZE,
            fontweight="bold",
            color=self.TEXT
        )

    # ============================================================
    # LINE GRAPH
    # ============================================================

    def draw_line(
        self,
        ax,
        dates,
        values,
        color,
        fill=True
    ):
        if not dates or not values:
            return

        ax.plot(
            dates,
            values,
            color=color,
            linewidth=self.LINE_WIDTH,
            marker="o",
            markersize=self.MARKER_SIZE,
            markerfacecolor=color,
            markeredgewidth=0,
            solid_capstyle="round"
        )

        if fill:
            ax.fill_between(
                dates,
                values,
                min(values),
                color=color,
                alpha=0.07
            )

    # ============================================================
    # 01 — OVERVIEW
    # ============================================================

    def overview_graph(self):
        data = self.data

        fig, ax = self.create_figure()
        ax.axis("off")

        fig.text(
            0.07,
            0.86,
            "MONTHLY OVERVIEW",
            fontsize=self.TITLE_SIZE,
            fontweight="bold",
            color=self.TEXT,
            ha="left"
        )

        steps = data["steps"]
        vo2 = data["vo2"]
        sleep = data["sleep"]
        stress = data["stress"]

        # AVERAGE STEPS
        fig.text(
            0.08,
            0.62,
            f'{steps["steps"]["avg"]:,.0f}',
            fontsize=self.NUMBER_SIZE,
            fontweight="bold",
            color=self.STEPS_COLOR,
            ha="left"
        )

        fig.text(
            0.08,
            0.53,
            "AVERAGE STEPS / DAY",
            fontsize=self.CAPTION_SIZE,
            fontweight="bold",
            color=self.TICKS,
            ha="left"
        )

        # AVERAGE VO2 MAX
        fig.text(
            0.38,
            0.62,
            f'{vo2["avg"]:.1f}',
            fontsize=self.NUMBER_SIZE,
            fontweight="bold",
            color=self.VO2_COLOR,
            ha="left"
        )

        fig.text(
            0.38,
            0.53,
            "AVERAGE VO₂ MAX",
            fontsize=self.CAPTION_SIZE,
            fontweight="bold",
            color=self.TICKS,
            ha="left"
        )

        # AVERAGE SLEEP
        avg_sleep = sleep["sleep_length"]["avg"]

        if avg_sleep is not None:
            total_minutes = round(avg_sleep * 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            sleep_text = f"{hours}h {minutes:02d}m"
        else:
            sleep_text = "—"

        fig.text(
            0.68,
            0.62,
            sleep_text,
            fontsize=52,
            fontweight="bold",
            color=self.SLEEP_COLOR,
            ha="left"
        )

        fig.text(
            0.68,
            0.53,
            "AVERAGE SLEEP / NIGHT",
            fontsize=self.CAPTION_SIZE,
            fontweight="bold",
            color=self.TICKS,
            ha="left"
        )

        # AVERAGE STRESS
        fig.text(
            0.08,
            0.31,
            f'{stress["avg_avg"]:.0f}',
            fontsize=self.NUMBER_SIZE,
            fontweight="bold",
            color=self.STRESS_COLOR,
            ha="left"
        )

        fig.text(
            0.08,
            0.22,
            "AVERAGE STRESS",
            fontsize=self.CAPTION_SIZE,
            fontweight="bold",
            color=self.TICKS,
            ha="left"
        )

        # AVERAGE DISTANCE
        fig.text(
            0.38,
            0.31,
            f'{steps["distance"]["avg"]:.1f}',
            fontsize=self.NUMBER_SIZE,
            fontweight="bold",
            color=self.TEXT,
            ha="left"
        )

        fig.text(
            0.38,
            0.22,
            "AVERAGE MILES / DAY",
            fontsize=self.CAPTION_SIZE,
            fontweight="bold",
            color=self.TICKS,
            ha="left"
        )

        # TOTAL STEPS
        fig.text(
            0.68,
            0.31,
            f'{steps["totals"]["steps"]:,.0f}',
            fontsize=52,
            fontweight="bold",
            color=self.TEXT,
            ha="left"
        )

        fig.text(
            0.68,
            0.22,
            "TOTAL STEPS",
            fontsize=self.CAPTION_SIZE,
            fontweight="bold",
            color=self.TICKS,
            ha="left"
        )

        self.save_graph(fig, "01_overview.png")

    # ============================================================
    # 02 — STEPS
    # ============================================================

    def steps_graph(self):
        fig, ax = self.create_figure()

        daily = self.data["steps"]["steps"]["daily"]
        dates, values = self.convert_dates(daily)

        self.draw_line(
            ax,
            dates,
            values,
            self.STEPS_COLOR
        )

        self.annotate_extremes(
            ax,
            dates,
            values,
            self.STEPS_COLOR
        )

        ax.set_title(
            "Daily Steps",
            loc="left",
            pad=25,
            fontsize=self.TITLE_SIZE,
            color=self.TEXT,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Date",
            labelpad=15,
            fontsize=self.AXIS_LABEL_SIZE
        )

        ax.set_ylabel(
            "Steps",
            labelpad=15,
            fontsize=self.AXIS_LABEL_SIZE
        )

        ax.set_ylim(bottom=0)

        self.date_axis(ax)
        self.style_axis(ax)

        fig.subplots_adjust(
            left=0.08,
            right=0.97,
            top=0.88,
            bottom=0.18
        )

        self.save_graph(
            fig,
            "02_steps.png"
        )

    # ============================================================
    # 03 — VO2 MAX
    # ============================================================

    def vo2_graph(self):
        fig, ax = self.create_figure()

        values = self.data["vo2"]["values"]

        if not values:
            plt.close(fig)
            return

        x = list(range(1, len(values) + 1))

        ax.plot(
            x,
            values,
            color=self.VO2_COLOR,
            linewidth=self.LINE_WIDTH,
            marker="o",
            markersize=self.MARKER_SIZE,
            markerfacecolor=self.VO2_COLOR,
            markeredgewidth=0
        )

        ax.fill_between(
            x,
            values,
            min(values),
            color=self.VO2_COLOR,
            alpha=0.07
        )

        high_index = values.index(max(values))
        high_value = values[high_index]

        ax.scatter(
            x[high_index],
            high_value,
            color=self.VO2_COLOR,
            s=110,
            zorder=10,
            edgecolors=self.TEXT,
            linewidths=2
        )

        ax.annotate(
            f"HIGH  {high_value:.1f}",
            xy=(x[high_index], high_value),
            xytext=(0, 28),
            textcoords="offset points",
            ha="center",
            fontsize=self.EXTREME_LABEL_SIZE,
            fontweight="bold",
            color=self.TEXT
        )

        low_index = values.index(min(values))
        low_value = values[low_index]

        ax.scatter(
            x[low_index],
            low_value,
            color=self.VO2_COLOR,
            s=110,
            zorder=10,
            edgecolors=self.TEXT,
            linewidths=2
        )

        ax.annotate(
            f"LOW  {low_value:.1f}",
            xy=(x[low_index], low_value),
            xytext=(0, -35),
            textcoords="offset points",
            ha="center",
            fontsize=self.EXTREME_LABEL_SIZE,
            fontweight="bold",
            color=self.TEXT
        )

        ax.set_title(
            "VO₂ Max",
            loc="left",
            pad=25,
            fontsize=self.TITLE_SIZE,
            color=self.TEXT,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Measurement",
            labelpad=15,
            fontsize=self.AXIS_LABEL_SIZE
        )

        ax.set_ylabel(
            "VO₂ Max",
            labelpad=15,
            fontsize=self.AXIS_LABEL_SIZE
        )

        ax.xaxis.set_major_locator(
            MaxNLocator(integer=True, nbins=8)
        )

        self.style_axis(ax)

        fig.subplots_adjust(
            left=0.08,
            right=0.97,
            top=0.88,
            bottom=0.18
        )

        self.save_graph(
            fig,
            "03_vo2_max.png"
        )

    # ============================================================
    # 04 — SLEEP
    # ============================================================

    def sleep_graph(self):
        fig, ax = self.create_figure()

        scores = self.data["sleep"]["daily"]["scores"]
        dates, values = self.convert_dates(scores)

        self.draw_line(
            ax,
            dates,
            values,
            self.SLEEP_COLOR
        )

        self.annotate_extremes(
            ax,
            dates,
            values,
            self.SLEEP_COLOR
        )

        ax.set_title(
            "Sleep Score",
            loc="left",
            pad=25,
            fontsize=self.TITLE_SIZE,
            color=self.TEXT,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Date",
            labelpad=15,
            fontsize=self.AXIS_LABEL_SIZE
        )

        ax.set_ylabel(
            "Sleep Score",
            labelpad=15,
            fontsize=self.AXIS_LABEL_SIZE
        )

        ax.set_ylim(0, 100)

        self.date_axis(ax)
        self.style_axis(ax)

        fig.subplots_adjust(
            left=0.08,
            right=0.97,
            top=0.88,
            bottom=0.18
        )

        self.save_graph(
            fig,
            "04_sleep.png"
        )

    # ============================================================
    # 05 — STRESS
    # ============================================================

    def stress_graph(self):
        fig, ax = self.create_figure()

        daily = self.data["stress"]["daily"]["average"]
        dates, values = self.convert_dates(daily)

        self.draw_line(
            ax,
            dates,
            values,
            self.STRESS_COLOR
        )

        self.annotate_extremes(
            ax,
            dates,
            values,
            self.STRESS_COLOR
        )

        ax.set_title(
            "Daily Stress",
            loc="left",
            pad=25,
            fontsize=self.TITLE_SIZE,
            color=self.TEXT,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Date",
            labelpad=15,
            fontsize=self.AXIS_LABEL_SIZE
        )

        ax.set_ylabel(
            "Stress Level",
            labelpad=15,
            fontsize=self.AXIS_LABEL_SIZE
        )

        ax.set_ylim(0, 100)

        self.date_axis(ax)
        self.style_axis(ax)

        fig.subplots_adjust(
            left=0.08,
            right=0.97,
            top=0.88,
            bottom=0.18
        )

        self.save_graph(
            fig,
            "05_stress.png"
        )

    # ============================================================
    # 06 — HEART RATE
    # ============================================================

    def heart_rate_graph(self):
        fig, ax = self.create_figure()

        heart_rate = self.data["heart_rate"]

        resting = heart_rate["resting"]["daily"]
        maximum = heart_rate["max"]["daily"]

        # RESTING
        resting_dates, resting_values = self.convert_dates(resting)

        ax.plot(
            resting_dates,
            resting_values,
            color=self.HEART_RESTING_COLOR,
            linewidth=self.LINE_WIDTH,
            marker="o",
            markersize=self.MARKER_SIZE,
            markerfacecolor=self.HEART_RESTING_COLOR,
            markeredgewidth=0,
            label="Resting"
        )

        self.annotate_extremes(
            ax,
            resting_dates,
            resting_values,
            self.HEART_RESTING_COLOR
        )

        # MAXIMUM
        max_dates, max_values = self.convert_dates(maximum)

        ax.plot(
            max_dates,
            max_values,
            color=self.HEART_MAX_COLOR,
            linewidth=self.LINE_WIDTH,
            marker="o",
            markersize=self.MARKER_SIZE,
            markerfacecolor=self.HEART_MAX_COLOR,
            markeredgewidth=0,
            alpha=0.75,
            label="Maximum"
        )

        self.annotate_extremes(
            ax,
            max_dates,
            max_values,
            self.HEART_MAX_COLOR
        )

        ax.set_title(
            "Heart Rate",
            loc="left",
            pad=25,
            fontsize=self.TITLE_SIZE,
            color=self.TEXT,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Date",
            labelpad=15,
            fontsize=self.AXIS_LABEL_SIZE
        )

        ax.set_ylabel(
            "Heart Rate (BPM)",
            labelpad=15,
            fontsize=self.AXIS_LABEL_SIZE
        )

        self.date_axis(ax)
        self.style_axis(ax)

        legend = ax.legend(
            frameon=False,
            fontsize=17,
            loc="upper right"
        )

        for label in legend.get_texts():
            label.set_color(self.TEXT)

        fig.subplots_adjust(
            left=0.08,
            right=0.97,
            top=0.88,
            bottom=0.18
        )

        self.save_graph(
            fig,
            "06_heart_rate.png"
        )

    # ============================================================
    # GENERATE ALL
    # ============================================================

    def generate_all(self):
        if not self.setup_output_folder():
            return False

        print()
        print("=" * 60)
        print("GENERATING GARMIN GRAPHS")
        print("=" * 60)

        self.overview_graph()
        self.steps_graph()
        self.vo2_graph()
        self.sleep_graph()
        self.stress_graph()
        self.heart_rate_graph()

        print()
        print("=" * 60)
        print("GARMIN GRAPH GENERATION COMPLETE")
        print("=" * 60)
        print("Format : 16:9 landscape")
        print("Size   : 1920 × 1080")
        print("Slides : 6")
        print(f"Output : {self.output_dir}")
        print("=" * 60)

        return True
