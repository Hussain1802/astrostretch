from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from astropy.io import fits


st.set_page_config(
    page_title="AstroStretch",
    page_icon="🔭",
    layout="wide",
)


def make_image_figure(image):
    """Create a borderless image figure that matches Streamlit's dark background."""
    figure, axis = plt.subplots(
        figsize=(7, 7),
        facecolor="#0e1117",
    )

    axis.imshow(
        image,
        cmap="gray",
        origin="lower",
    )

    axis.axis("off")
    axis.set_position([0, 0, 1, 1])

    figure.subplots_adjust(
        left=0,
        right=1,
        bottom=0,
        top=1,
    )

    return figure


def apply_stretch(image, method, strength):
    """Apply the selected brightness transformation."""
    if method == "Linear":
        return image

    if method == "Logarithmic":
        return np.log1p(strength * image) / np.log1p(strength)

    return np.arcsinh(strength * image) / np.arcsinh(strength)


st.title("AstroStretch")
st.caption(
    "Explore faint detail hidden inside astronomical FITS images."
)

uploaded_file = st.file_uploader(
    "Upload a FITS image",
    type=["fits", "fit", "fts"],
)

if uploaded_file is None:
    st.info("Upload a telescope image to begin.")
    st.stop()


# Search the FITS file for the first usable two-dimensional image.
image_data = None
image_header = None

try:
    uploaded_file.seek(0)

    with fits.open(uploaded_file, memmap=False) as hdul:
        for hdu in hdul:
            if hdu.data is None:
                continue

            candidate = np.squeeze(np.asarray(hdu.data))

            if candidate.ndim == 2:
                image_data = candidate.astype(np.float32)
                image_header = hdu.header.copy()
                break

except Exception as error:
    st.error(f"The FITS file could not be opened: {error}")
    st.stop()


if image_data is None:
    st.error("No two-dimensional image was found in this FITS file.")
    st.stop()


finite_pixels = image_data[np.isfinite(image_data)]

if finite_pixels.size == 0:
    st.error("This image contains no usable pixel values.")
    st.stop()


height, width = image_data.shape
minimum_value = float(np.min(finite_pixels))
median_value = float(np.median(finite_pixels))
maximum_value = float(np.max(finite_pixels))
dynamic_range = maximum_value - minimum_value


st.success(f"Loaded {uploaded_file.name}")

stats_columns = st.columns(4)

stats_columns[0].metric(
    "Image size",
    f"{width} × {height}",
)

stats_columns[1].metric(
    "Usable pixels",
    f"{finite_pixels.size:,}",
)

stats_columns[2].metric(
    "Median value",
    f"{median_value:,.2f}",
)

stats_columns[3].metric(
    "Dynamic range",
    f"{dynamic_range:,.2f}",
)


with st.expander("FITS details"):
    object_name = image_header.get("OBJECT", "Not recorded")
    filter_name = image_header.get("FILTER", "Not recorded")
    exposure = image_header.get("EXPTIME", "Not recorded")
    observation_date = image_header.get("DATE-OBS", "Not recorded")

    metadata_columns = st.columns(4)

    metadata_columns[0].write("**Object**")
    metadata_columns[0].write(object_name)

    metadata_columns[1].write("**Filter**")
    metadata_columns[1].write(filter_name)

    metadata_columns[2].write("**Exposure**")
    metadata_columns[2].write(exposure)

    metadata_columns[3].write("**Observation date**")
    metadata_columns[3].write(observation_date)


st.divider()
st.subheader("Stretch controls")

method_column, black_column, white_column = st.columns(3)

with method_column:
    stretch_method = st.selectbox(
        "Stretch method",
        options=[
            "Linear",
            "Logarithmic",
            "Asinh",
        ],
        index=2,
    )

with black_column:
    black_percentile = st.slider(
        "Black point percentile",
        min_value=0.0,
        max_value=10.0,
        value=1.0,
        step=0.1,
    )

with white_column:
    white_percentile = st.slider(
        "White point percentile",
        min_value=90.0,
        max_value=100.0,
        value=99.5,
        step=0.1,
    )


strength_disabled = stretch_method == "Linear"

stretch_strength = st.slider(
    "Stretch strength",
    min_value=1.0,
    max_value=20.0,
    value=4.0,
    step=0.5,
    disabled=strength_disabled,
)

if stretch_method == "Linear":
    st.caption(
        "Linear keeps evenly spaced brightness values evenly spaced."
    )
elif stretch_method == "Logarithmic":
    st.caption(
        "Logarithmic stretching strongly lifts faint pixels while compressing bright ones."
    )
else:
    st.caption(
        "Asinh stretching reveals faint structure while keeping bright regions relatively controlled."
    )


black_point = np.percentile(
    finite_pixels,
    black_percentile,
)

white_point = np.percentile(
    finite_pixels,
    white_percentile,
)

if white_point <= black_point:
    st.error("The white point must be greater than the black point.")
    st.stop()


scaled_image = (
    (image_data - black_point)
    / (white_point - black_point)
)

scaled_image = np.nan_to_num(
    scaled_image,
    nan=0.0,
    posinf=1.0,
    neginf=0.0,
)

scaled_image = np.clip(
    scaled_image,
    0,
    1,
)

stretched_image = apply_stretch(
    scaled_image,
    stretch_method,
    stretch_strength,
)


st.divider()

raw_column, stretched_column = st.columns(2)

with raw_column:
    st.subheader("Original view")

    raw_figure = make_image_figure(image_data)

    st.pyplot(
        raw_figure,
        use_container_width=True,
    )

    plt.close(raw_figure)

with stretched_column:
    st.subheader(f"{stretch_method} stretch")

    stretched_figure = make_image_figure(stretched_image)

    st.pyplot(
        stretched_figure,
        use_container_width=True,
    )

    plt.close(stretched_figure)


st.divider()
st.subheader("Pixel-value histogram")

# Extreme values can squash the useful part of a histogram,
# so the graph focuses on the central 99.8% of the pixels.
histogram_low = np.percentile(finite_pixels, 0.1)
histogram_high = np.percentile(finite_pixels, 99.9)

histogram_pixels = finite_pixels[
    (finite_pixels >= histogram_low)
    & (finite_pixels <= histogram_high)
]

# Limit the number of plotted pixels so very large files remain responsive.
if histogram_pixels.size > 250_000:
    sample_step = histogram_pixels.size // 250_000
    histogram_pixels = histogram_pixels[::sample_step]


histogram_figure, histogram_axis = plt.subplots(
    figsize=(10, 4),
    facecolor="#0e1117",
)

histogram_axis.set_facecolor("#0e1117")

histogram_axis.hist(
    histogram_pixels,
    bins=120,
    color="#7f8c8d",
)

histogram_axis.axvline(
    black_point,
    color="#ff4b4b",
    linewidth=2,
    label="Black point",
)

histogram_axis.axvline(
    white_point,
    color="#4ba3ff",
    linewidth=2,
    label="White point",
)

histogram_axis.set_yscale("log")
histogram_axis.set_xlabel("Pixel value")
histogram_axis.set_ylabel("Number of pixels")
histogram_axis.legend()

histogram_axis.tick_params(
    colors="white",
)

histogram_axis.xaxis.label.set_color("white")
histogram_axis.yaxis.label.set_color("white")

for spine in histogram_axis.spines.values():
    spine.set_color("#555555")

histogram_figure.tight_layout()

st.pyplot(
    histogram_figure,
    use_container_width=True,
)

plt.close(histogram_figure)

st.caption(
    "The red and blue lines show the pixel values currently being used "
    "as the black and white display limits."
)


png_buffer = BytesIO()

plt.imsave(
    png_buffer,
    stretched_image,
    cmap="gray",
    vmin=0,
    vmax=1,
    origin="lower",
    format="png",
)

png_buffer.seek(0)

download_name = (
    uploaded_file.name.rsplit(".", 1)[0]
    + "_stretched.png"
)

st.download_button(
    label="Download stretched PNG",
    data=png_buffer.getvalue(),
    file_name=download_name,
    mime="image/png",
)

st.caption(
    "The downloaded PNG contains the displayed version. "
    "The original FITS measurements are not changed."
)