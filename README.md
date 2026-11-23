# Beam Designer

Beam Designer is a small desktop tool for exploring single-span beam behavior. Set a span and support condition, add point and uniform loads, choose a steel or lumber section, and inspect the shear, moment, and deflection response alongside basic bending and deflection checks. The plots update as the inputs change.

> **Scope:** This is an educational and preliminary sizing aid. It checks flexural stress and elastic deflection for simply supported beams and left-fixed cantilevers. It does not check self-weight, shear stress, lateral-torsional buckling, load combinations, or continuous beams. Confirm assumptions and design requirements independently before using results for construction.

## Example beam cases

The diagrams below sketch the four calculation examples used for validation. The moment shapes are schematic; values and support reactions are listed below and are calculated by the app.

![Four Beam Designer validation examples showing the beam and load arrangement with corresponding moment diagrams](docs/figures/validation-examples.svg)

| Case | Beam and loading | Reference results |
|---|---|---|
| 1 | 20 ft simply supported, W12x26, 1 kip/ft across the span | Reactions 10 k each; max shear 10 k; max moment 50 kip-ft at midspan; bending stress 17.96 ksi; max deflection 0.609 in; L/360 = 0.667 in |
| 2 | 20 ft simply supported, W12x26, 10 kip point load at 5 ft | Reactions 7.5 k and 2.5 k; max moment 37.5 kip-ft at 5 ft; bending stress 13.47 ksi; max deflection about 0.340 in near 8.82 ft |
| 3 | 10 ft cantilever, W12x26, 5 kip at the free end | Fixed reaction 5 k and fixed-end moment 50 kip-ft; max deflection about 0.487 in at the free end; L/360 = 0.333 in |
| 4 | 12 ft simply supported, 2x10, 0.05 kip/ft across the span | Max moment 0.90 kip-ft; bending stress 0.505 ksi; max deflection 0.147 in |

## Requirements and launch

- Python 3.10 or newer
- NumPy and Matplotlib (Tkinter is included with most standard Python installations; on some Linux distributions it is a separate system package)

Install the Python packages and launch from the project directory:

```powershell
python -m pip install -r requirements.txt
python app.py
```

The app starts with Case 1 loaded. The left panel controls support type, span, loads, material, section, and the L/240 or L/360 deflection limit. Add and remove loads with the buttons and × controls. Edit the numeric fields to update the analysis; point loads can also be dragged along the beam and snap to quarter-foot positions. Use the dark-mode toggle to change the plot theme.

The plots show the beam and loads, followed by shear, moment, and deflection diagrams. Hover over a diagram to inspect values at a span location. The check cards compare bending stress with the material allowable and maximum deflection with the selected span limit. The recommendation offers the lightest passing steel section (weight ties favor larger Ix), or the first passing lumber entry in the table. **Use section** selects that recommendation.

## Equations and conventions

The model uses downward load magnitudes as positive input values. Lengths are entered in feet, forces in kips, and distributed loads in kips per foot. Moment is reported in kip-ft; deflection is reported in inches. Reactions and internal actions use static equilibrium. The app ignores self-weight.

### Resultant loads and reactions

For a point load $P_i$ at $a_i$, the resultant is $P_i$ at $a_i$. A uniform load $w_j$ from $a_j$ to $b_j$ is replaced by its equivalent force and centroid:

$$
\begin{aligned}
Q_j &= w_j (b_j-a_j) && \text{resultant force (kips)} \\
x_{Q_j} &= \frac{a_j+b_j}{2} && \text{resultant location (ft)}
\end{aligned}
$$

Let $W$ be the sum of all resultant forces and $J$ their first moment about the left end. For a simply supported span $L$:

$$
\begin{aligned}
R_{\mathrm{right}} &= \frac{J}{L}, \\
R_{\mathrm{left}} &= W-R_{\mathrm{right}}.
\end{aligned}
$$

For a cantilever fixed at the left end:

$$
\begin{aligned}
R_{\mathrm{left}} &= W, \\
M_{\mathrm{fixed}} &= J.
\end{aligned}
$$

### Shear and bending moment

For a simply supported beam, at a section $x$, let $c_j(x)=\min(x,b_j)$ and $\ell_j(x)=\max(0,c_j(x)-a_j)$ be the portion of uniform-load segment $j$ to the left of the section. Let $H$ denote the unit step function. The internal shear and moment are:

$$
\begin{aligned}
V(x) &= R_{\mathrm{left}} - \sum_i P_i H(x-a_i) - \sum_j w_j\ell_j(x), \\
M(x) &= R_{\mathrm{left}}x - \sum_i P_i\max(0,x-a_i) \\
     &\quad - \sum_j w_j\ell_j(x)\left(x-\frac{a_j+c_j(x)}{2}\right).
\end{aligned}
$$

For a cantilever, use the loads to the right of the section. Define $\ell_j^{r}(x)=\max(0,b_j-\max(x,a_j))$:

$$
\begin{aligned}
V(x) &= -\sum_i P_i\mathbf{1}_{a_i\ge x} - \sum_j w_j\ell_j^{r}(x), \\
M(x) &= -\sum_i P_i\max(0,a_i-x) \\
     &\quad - \sum_j w_j\ell_j^{r}(x)\left(\frac{\max(x,a_j)+b_j}{2}-x\right),
\end{aligned}
$$

where $\mathbf{1}_{a_i\ge x}$ is 1 when the point load lies at or to the right of $x$, and 0 otherwise. Every load segment is clipped to the beam span. These equations use the implementation's downward-positive load convention; checks use the absolute maximum moment.

### Elastic deflection and checks

The software integrates the elastic beam equation numerically over a span grid containing regular samples, point-load locations, and uniform-load boundaries. Curvature, slope, and displacement satisfy:

$$
\begin{aligned}
\kappa(x) &= \frac{M(x)}{EI}, \\
\frac{d\theta}{dx} &= \kappa(x), \\
\frac{dy}{dx} &= \theta(x).
\end{aligned}
$$

The trapezoidal rule integrates curvature to slope and slope to displacement. For a simply supported beam, a linear correction enforces $y(0)=y(L)=0$. For a cantilever, the integration starts with $y(0)=0$ and $\theta(0)=0$. The reported maximum deflection is the largest absolute sampled displacement.

Bending stress and the selected deflection limit are:

$$
\begin{aligned}
f_b &= \frac{12\lvert M_{\max}\rvert}{S_x} && \text{(ksi, with $M_{\max}$ in kip-ft)}, \\
\delta_{\mathrm{allow}} &= \frac{12L}{n} && \text{(in, with $L$ in ft and $n\in\{240,360\}$)}.
\end{aligned}
$$

The checks pass when $f_b\le F_b$ and $\lvert y\rvert_{\max}\le\delta_{\mathrm{allow}}$. Here $E$ is in ksi, $I$ is in in$^4$, and $S_x$ is in in$^3$. The factor of 12 converts kip-ft to kip-in in the stress equation. The listed material properties and sections are in [spec.md](spec.md). The app uses the selected section's $E$ and $I$ for its displayed deflection; when evaluating a recommendation, it scales deflection inversely with each candidate's $I$.

## Validation tests

Run the analysis tests from the repository root:

```powershell
python -m unittest discover -s tests -v
```

The tests cover the four examples above and load clipping/zero-length uniform-load behavior. They test the calculation module without opening the desktop window.
