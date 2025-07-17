# Gravity Turn

## 🚀 Introduction

The **gravity&nbsp;turn** is the most widely used ascent strategy in rocketry.  After clearing the launch tower a vehicle pitches slightly, then lets **gravity itself rotate the velocity vector** toward the local horizontal while engines continue to accelerate.  This technique is important because it

* maintains a *very small angle of attack*, minimising aerodynamic stress;
* distributes thrust efficiently between raising altitude and building orbital speed;
* requires only gentle guidance inputs once the initial pitch-over is set.

In short, a well-executed gravity turn yields a *lighter*, *safer* and *more efficient* ascent.

---

## 🔬 Physics

We idealise the launch vehicle as a point mass experiencing

* **central gravity** characterised by the parameter \(\mu\),
* **thrust** magnitude \(T\) applied at a gimbal angle \(\alpha\),
* optional aerodynamic **lift** \(L\) and **drag** \(D\), and
* a *decreasing mass* \(m(t)\) due to propellant flow \(\dot m_{\text{prop}}>0\).

Using polar coordinates centred on the planet, the state vector is \((r,\,\gamma,\,v,\,m)\) where
\(r\) is radius, \(\gamma\) the flight-path angle (>0 above the horizon), and \(v\) the inertial speed.  The full planar ODE system is

\[\begin{aligned}
\dot r      &= v\,\sin\gamma,\\[2pt]
\dot\gamma &= \frac{v}{r}\cos\gamma\; - \; \frac{\mu}{r^{2}v}\cos\gamma\; + \; \frac{T}{m v}\cos\alpha\; + \; \frac{L}{m v},\\[4pt]
\dot v      &= \frac{T}{m} - g(r)\,\sin\gamma - \frac{D}{m},\\[4pt]
\dot m      &= -\dot m_{\text{prop}}.
\end{aligned}\]

with local gravity \(g(r)=\mu/r^{2}\).

### Why does the code integrate **only** \(\dot\gamma\)?

`core/launch/gt.py` receives *measured* values of \(r\), \(v\) and \(m\) from kRPC every 50&nbsp;ms.  The sole quantity it must *predict* is the *future orientation* of the velocity vector, captured by \(\gamma\).  Propagating just

```python
gamma_dot = dgamma_dt(v, r, gamma, mu, T, m)  # α=L=0
gamma_next = gamma + gamma_dot * dt            # Forward-Euler
```

keeps guidance lightweight while still honouring the underlying physics.

---

## 📝 Variables

| Symbol | Python stream / value | Description |
|--------|-----------------------|-------------|
| \(v\) | `SPEED()` | Inertial speed magnitude [m s⁻¹] |
| \(r\) | `RADIUS()` | Distance from planet centre [m] |
| \(\gamma\) | `atan2(V_VERT(), V_HORIZ())` | Flight-path angle [rad] |
| \(\mu\) | `body.gravitational_parameter` | Gravitational parameter [m³ s⁻²] |
| \(T\) | `THRUST()` | Available thrust [N] |
| \(m\) | `MASS()` | Vehicle mass [kg] |
| \(\alpha\) | 0 (assumed) | Gimbal angle rel. to velocity [rad] |
| \(L\) | 0 (neglected) | Aerodynamic lift [N] |
| \(D\) | 0 (neglected) | Aerodynamic drag [N] |

All of these feed directly into `dgamma_dt()` from `core/utils/formulas.py`.

---

## ➗ Formula & Code Mapping

In `core/utils/formulas.py` the function implementing the key derivative is

```python
def dgamma_dt(v, r, gamma, μ, T, m, *, alpha=0.0, L=0.0):
    """Flight-path angle rate for the full gravity-turn model."""
    return (
        (v / r) * math.cos(gamma)          # geometry term
        - (μ / (r**2 * v)) * math.cos(gamma)  # gravity gradient
        + (T / (m * v)) * math.cos(alpha)     # thrust component
        + (L / (m * v))                       # aerodynamic lift
    )
```

which is the literal Python translation of

\[\dot\gamma = \frac{v}{r}\cos\gamma - \frac{\mu}{r^{2}v}\cos\gamma + \frac{T}{m v}\cos\alpha + \frac{L}{m v}.\]

When the **classical** assumptions \(\alpha=L=D=0\) hold, the guidance loop in `gt.py` reduces to

```python
gamma_dot = dgamma_dt(v, r, gamma, mu, T, m)  # simplified automatically
pitch_cmd = clamp(90.0 - math.degrees(gamma + gamma_dot*dt), 0.0, 90.0)
ap.target_pitch_and_heading(pitch_cmd, 90)
```

Thus the physics, mathematics, and code align *one-to-one*.

---

*Last updated: {{< DATE_PLACEHOLDER >}}*
