import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(page_title=" antenna applications", layout="wide")

# ------------------------------------------------
# 🎨 CSS (UNCHANGED)
# ------------------------------------------------
st.markdown("""
<style>
.main {
    background: linear-gradient(135deg, #1f4037, #99f2c8);
}
h1 {
    text-align: center;
    color: white;
}
.card {
    background: rgba(255,255,255,0.9);
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    margin-bottom: 20px;
}
[data-testid="stMetric"] {
    background: white;
    padding: 15px;
    border-radius: 12px;
}
[data-testid="stMetricValue"] {
    color: black !important;
    font-size: 28px !important;
    font-weight: bold;
}
[data-testid="stMetricLabel"] {
    color: #444 !important;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2027, #203a43, #2c5364);
    color: white;
}
.footer {
    background: white;
    padding: 25px;
    border-radius: 15px;
}
</style>
""", unsafe_allow_html=True)

st.title("📡 Antenna applications")
st.markdown("---")

# ------------------------------------------------
# MODE SELECTOR
# ------------------------------------------------
mode = st.sidebar.selectbox("Select Mode", ["Antenna Design", "phased array detection"])


# =================================================
# 🔵 MODE 1: YOUR ORIGINAL CODE (UNCHANGED)
# =================================================
if mode == "Antenna Design":

    st.sidebar.title("⚙️ Controls")

    antenna_type = st.sidebar.selectbox(
        "Antenna Type",
        ["Microstrip Patch", "UPA", "ULA"]
    )

    freq = st.sidebar.number_input("Frequency (GHz)", value=3.5)
    h = st.sidebar.number_input("Substrate Height (mm)", value=1.6) * 1e-3

    materials = {
        "FR4": {"er": 4.4, "loss": 0.02},
        "Rogers RT5880": {"er": 2.2, "loss": 0.0009},
        "Rogers RT6006": {"er": 6.15, "loss": 0.0027},
        "Air": {"er": 1.0, "loss": 0.0}
    }

    mat_choice = st.sidebar.selectbox("Substrate Material", list(materials.keys()))
    er = materials[mat_choice]["er"]

    metals = {
        "Copper": 5.8e7,
        "Aluminum": 3.5e7,
        "Gold": 4.1e7
    }

    metal_choice = st.sidebar.selectbox("Metal", list(metals.keys()))
    conductivity = metals[metal_choice]

    c = 3e8
    f = freq * 1e9
    wavelength = c / f

    W = (c/(2*f))*np.sqrt(2/(er+1))
    eeff = ((er+1)/2)+((er-1)/2)*(1+12*h/W)**(-0.5)

    deltaL = 0.412*h*((eeff+0.3)*(W/h+0.264))/((eeff-0.258)*(W/h+0.8))
    L = (c/(2*f*np.sqrt(eeff))) - 2*deltaL

    Rin = 90*(er**2)/(er-1)*(L/W)

    def microstrip_width(Z0, er, h):
        A = Z0/60*np.sqrt((er+1)/2)
        return (8*np.exp(A))/(np.exp(2*A)-2)*h

    Wf = microstrip_width(50, er, h)
    Lf = wavelength/(4*np.sqrt(eeff))
    y0 = (L/np.pi)*np.arccos(np.sqrt(50/Rin))

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📐 Patch")

    c1,c2,c3 = st.columns(3)
    c1.metric("Width (mm)", round(W*1000,2))
    c2.metric("Length (mm)", round(L*1000,2))
    c3.metric("εeff", round(eeff,3))

    c4,c5 = st.columns(2)
    c4.metric("ΔL (mm)", round(deltaL*1000,3))
    c5.metric("Rin (Ω)", round(Rin,2))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🔌 Feed")

    c6,c7,c8 = st.columns(3)
    c6.metric("Wf (mm)", round(Wf*1000,2))
    c7.metric("Lf (mm)", round(Lf*1000,2))
    c8.metric("Inset y0 (mm)", round(y0*1000,2))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📡 Export to CST")

    def cst_macro():
        return f'''
Sub Main()

With Material
.Name "{mat_choice}"
.Epsilon "{er}"
.Create
End With

End Sub
'''

    st.download_button("Download CST Macro", cst_macro(), "antenna.bas")

    st.markdown("<div class='footer'>", unsafe_allow_html=True)
    st.write("All geometry values are displayed in millimeters (mm).")
    st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# 🔴 MODE 2: CSI MODULE (FINAL WITH INTERACTIVE 3D)
# =================================================
else:

    import plotly.graph_objects as go

    st.sidebar.title("📡 CSI Controls")

    # ---------------- ARRAY TYPE ----------------
    array_type = st.sidebar.selectbox("Array Type", ["ULA", "UPA"])

    if array_type == "ULA":
        N = st.sidebar.number_input("Number of Antennas", 2, 32, 8)
    else:
        Nx = st.sidebar.number_input("Nx", 2, 16, 4)
        Ny = st.sidebar.number_input("Ny", 2, 16, 4)
        N = Nx * Ny

    # ---------------- INPUT MODE ----------------
    input_mode = st.sidebar.selectbox("CSI Input Mode", ["Manual", "Upload File"])

    # ------------------------------------------------
    # CSI INPUT
    # ------------------------------------------------
    if input_mode == "Manual":

        real = st.text_input("Real Part", ",".join(["1"] * N))
        imag = st.text_input("Imag Part", ",".join(["0"] * N))

        try:
            real = np.array([float(x) for x in real.split(",")])
            imag = np.array([float(x) for x in imag.split(",")])
            H = real + 1j * imag
        except:
            st.error("Invalid input format")
            H = np.ones(N)

    else:
        file = st.file_uploader("Upload CSI (.npy or .csv)")

        if file is not None:
            try:
                if file.name.endswith(".npy"):
                    H_loaded = np.load(file)
                    H = H_loaded.flatten()
                else:
                    data = np.loadtxt(file, delimiter=",")
                    H = data[:, 0] + 1j * data[:, 1]
            except:
                st.error("Invalid file format")
                H = np.ones(N)
        else:
            H = np.ones(N)

    # ------------------------------------------------
    # NOISE
    # ------------------------------------------------
    noise_level = st.sidebar.slider("Noise Level", 0.0, 0.5, 0.0)
    noise = noise_level * (np.random.randn(*H.shape) + 1j*np.random.randn(*H.shape))
    H = H + noise

    # ------------------------------------------------
    # CSI MATRIX DISPLAY
    # ------------------------------------------------
    st.write("### 📊 CSI Matrix")

    if array_type == "ULA":
        H_matrix = H.reshape(-1, 1)
    else:
        H_matrix = H.reshape(Nx, Ny)

    st.dataframe(H_matrix)

    # ------------------------------------------------
    # CONSTANTS
    # ------------------------------------------------
    c = 3e8
    f = 3.5e9
    lam = c / f
    d = lam / 2
    k = 2 * np.pi / lam

    # =================================================
    # 📡 ULA DETECTION
    # =================================================
    if array_type == "ULA":

        st.subheader("📡 ULA Detection")

        theta_scan = np.linspace(-90, 90, 200)
        response = []

        for angle in theta_scan:
            theta = np.radians(angle)
            steering = np.exp(1j * k * np.arange(N) * d * np.sin(theta))
            val = np.abs(np.sum(H * np.conj(steering)))
            response.append(val)

        response = np.array(response)
        response /= np.max(response)

        main_angle = theta_scan[np.argmax(response)]
        st.success(f"Detected Angle: {main_angle:.2f}°")

        confidence = np.max(response)
        st.write(f"Confidence: {confidence:.2f}")

        peaks = np.argsort(response)[-3:]
        st.write("Top 3 detected angles:")
        st.write(np.sort(theta_scan[peaks]))

    # =================================================
    # 📡 UPA DETECTION + 3D PLOT
    # =================================================
    else:

        st.subheader("📡 UPA Detection")

        H_upa = H.reshape(Nx, Ny)

        theta_scan = np.linspace(0, 90, 40)
        phi_scan = np.linspace(-90, 90, 40)

        TH, PH = np.meshgrid(theta_scan, phi_scan)

        response = np.zeros_like(TH)

        # ORIGINAL LOOP (UNCHANGED)
        for i in range(len(theta_scan)):
            for j in range(len(phi_scan)):

                theta = np.radians(theta_scan[i])
                phi = np.radians(phi_scan[j])

                val = 0

                for m in range(Nx):
                    for n in range(Ny):

                        phase_shift = k * (
                            m * d * np.sin(theta) * np.cos(phi) +
                            n * d * np.sin(theta) * np.sin(phi)
                        )

                        val += H_upa[m, n] * np.exp(-1j * phase_shift)

                response[j, i] = np.abs(val)

        response /= np.max(response)

        # ---------------- DETECT PEAK ----------------
        max_idx = np.unravel_index(np.argmax(response), response.shape)

        theta_est = theta_scan[max_idx[1]]
        phi_est = phi_scan[max_idx[0]]

        st.success(f"Elevation θ: {theta_est:.2f}°")
        st.success(f"Azimuth φ: {phi_est:.2f}°")

        confidence = np.max(response)
        st.write(f"Confidence: {confidence:.2f}")

        # ---------------- MULTI SIGNAL ----------------
        flat = response.flatten()
        peaks = np.argsort(flat)[-3:]

        st.write("Top 3 detected directions:")
        for idx in peaks:
            i, j = np.unravel_index(idx, response.shape)
            st.write(f"θ={theta_scan[j]:.1f}°, φ={phi_scan[i]:.1f}°")

        # =================================================
        # 📡 INTERACTIVE 3D PLOT WITH PEAK
        # =================================================
        st.subheader("📡 3D Spatial Response")

        fig = go.Figure()

        # Surface
        fig.add_trace(go.Surface(
            x=TH,
            y=PH,
            z=response,
            colorscale='Viridis',
            opacity=0.9
        ))

        # 🔴 Peak highlight
        fig.add_trace(go.Scatter3d(
            x=[theta_est],
            y=[phi_est],
            z=[np.max(response)],
            mode='markers',
            marker=dict(size=6, color='red'),
            name='Detected Peak'
        ))

        fig.update_layout(
            scene=dict(
                xaxis_title='Elevation θ (deg)',
                yaxis_title='Azimuth φ (deg)',
                zaxis_title='Response'
            ),
            margin=dict(l=0, r=0, b=0, t=30)
        )

        st.plotly_chart(fig, use_container_width=True)