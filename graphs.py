import matplotlib.pyplot as plt
import numpy as np


def plot_hohmann_transfer_first_burn(m_a, r_1, r_2, filename="hohmann_transfer.png"):
    """
    Visualize a Hohmann transfer between two circular orbits and save to a file.

    Parameters:
        m_a (float): Mean altitude of the vessel above the central body [m]
        r_1 (float): Radius of the initial (vessel) circular orbit [m]
        r_2 (float): Radius of the target circular orbit [m]
        filename (str): Path to save the output image (default "hohmann_transfer.png")
    """
    # Central body at (0,0)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_aspect("equal")

    # Draw central body
    central_body_radius = r_1 - m_a
    central = plt.Circle(
        (0, 0), central_body_radius, color="gray", alpha=0.5, label="Central Body"
    )
    ax.add_artist(central)

    # Draw initial orbit
    orbit1 = plt.Circle(
        (0, 0), r_1, color="b", fill=False, linewidth=1, label="Initial Orbit (r₁)"
    )
    ax.add_artist(orbit1)

    # Draw target orbit
    orbit2 = plt.Circle(
        (0, 0), r_2, color="g", fill=False, linewidth=1, label="Target Orbit (r₂)"
    )
    ax.add_artist(orbit2)

    # Draw transfer ellipse
    a = (r_1 + r_2) / 2  # semi-major axis
    b = np.sqrt(r_1 * r_2)  # semi-minor axis (approximation for visualization)
    theta = np.linspace(0, 2 * np.pi, 500)
    x_ellipse = a * np.cos(theta) - (a - r_1)  # center ellipse at periapsis
    y_ellipse = b * np.sin(theta)
    ax.plot(x_ellipse, y_ellipse, "r--", linewidth=1, label="Transfer Ellipse")

    # Mark periapsis and apoapsis
    ax.plot([r_1, -r_2], [0, 0], "ro", markersize=6, label="Periapsis/Apoapsis")
    ax.text(r_1 * 1.02, 0, "Periapsis", color="r", va="center", ha="left", fontsize=10)
    ax.text(-r_2 * 1.02, 0, "Apoapsis", color="r", va="center", ha="right", fontsize=10)

    # Mark mean altitude
    if m_a > central_body_radius:
        ax.plot([m_a], [0], "ko", markersize=6, label="Mean Altitude")
        ax.text(
            m_a * 1.02,
            0,
            f"Mean Altitude\n({m_a / 1000:.1f} km)",
            color="k",
            va="bottom",
            ha="left",
            fontsize=9,
        )

    # Set limits and labels
    max_r = max(r_1, r_2) * 1.2
    ax.set_xlim(-max_r, max_r)
    ax.set_ylim(-max_r, max_r)
    ax.set_xlabel("Distance [m]")
    ax.set_ylabel("Distance [m]")
    ax.set_title("Hohmann Transfer Visualization (First Burn)")
    ax.legend(loc="upper right")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.savefig(filename, bbox_inches="tight", dpi=300)
    plt.close(fig)


def plot_hohmann_transfer_second_burn(
    m_a, r_1, r_2, filename="hohmann_transfer_second_burn.png"
):
    """
    Visualize the Hohmann transfer at the moment of the second burn (arrival at target orbit).

    Parameters:
        m_a (float): Mean altitude of the vessel above the central body [m]
        r_1 (float): Radius of the initial (vessel) circular orbit [m]
        r_2 (float): Radius of the target circular orbit [m]
        filename (str): Path to save the output image (default "hohmann_transfer_second_burn.png")
    """
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_aspect("equal")

    # Draw central body
    central_body_radius = r_1 - m_a
    central = plt.Circle(
        (0, 0), central_body_radius, color="gray", alpha=0.5, label="Central Body"
    )
    ax.add_artist(central)

    # Draw initial orbit
    orbit1 = plt.Circle(
        (0, 0), r_1, color="b", fill=False, linewidth=1, label="Initial Orbit (r₁)"
    )
    ax.add_artist(orbit1)

    # Draw target orbit
    orbit2 = plt.Circle(
        (0, 0), r_2, color="g", fill=False, linewidth=1, label="Target Orbit (r₂)"
    )
    ax.add_artist(orbit2)

    # Draw transfer ellipse (show only the half from periapsis to apoapsis)
    a = (r_1 + r_2) / 2  # semi-major axis
    b = np.sqrt(r_1 * r_2)  # semi-minor axis (approximation for visualization)
    # The transfer is from periapsis (theta=0) to apoapsis (theta=pi)
    theta = np.linspace(0, np.pi, 300)
    x_ellipse = a * np.cos(theta) - (a - r_1)
    y_ellipse = b * np.sin(theta)
    ax.plot(
        x_ellipse, y_ellipse, "r--", linewidth=1, label="Transfer Ellipse (completed)"
    )

    # Draw the second burn trajectory as a purple dotted circle on top of the target orbit
    theta_full = np.linspace(0, 2 * np.pi, 500)
    x_circ = r_2 * np.cos(theta_full)
    y_circ = r_2 * np.sin(theta_full)
    ax.plot(
        x_circ,
        y_circ,
        color="purple",
        linestyle="--",
        linewidth=1,
        label="Second Burn (Circularized Orbit)",
        zorder=3,
    )

    # Mark periapsis and apoapsis
    ax.plot([r_1, -r_2], [0, 0], "ro", markersize=6, label="Periapsis/Apoapsis")
    ax.text(r_1 * 1.02, 0, "Periapsis", color="r", va="center", ha="left", fontsize=10)
    ax.text(-r_2 * 1.02, 0, "Apoapsis", color="r", va="center", ha="right", fontsize=10)

    # Mark mean altitude
    if m_a > central_body_radius:
        ax.plot([m_a], [0], "ko", markersize=6, label="Mean Altitude")
        ax.text(
            m_a * 1.02,
            0,
            f"Mean Altitude\n({m_a / 1000:.1f} km)",
            color="k",
            va="bottom",
            ha="left",
            fontsize=9,
        )

    # Mark the vessel at the apoapsis (arrival point for second burn)
    ax.plot([-r_2], [0], "ms", markersize=10, label="Second Burn (Circularize)")
    ax.text(
        -r_2 * 1.05,
        0,
        "Second Burn\n(Circularize)",
        color="m",
        va="top",
        ha="right",
        fontsize=10,
    )

    # Set limits and labels
    max_r = max(r_1, r_2) * 1.2
    ax.set_xlim(-max_r, max_r)
    ax.set_ylim(-max_r, max_r)
    ax.set_xlabel("Distance [m]")
    ax.set_ylabel("Distance [m]")
    ax.set_title("Hohmann Transfer Visualization (Second Burn)")
    ax.legend(loc="upper right")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.savefig(filename, bbox_inches="tight", dpi=300)
    plt.close(fig)


# if __name__ == "__main__":
#     plot_hohmann_transfer(142000, 742000, 12000000)
