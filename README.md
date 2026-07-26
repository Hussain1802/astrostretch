# AstroStretch

AstroStretch is a small web app for exploring faint detail inside astronomical FITS images.

**Live app:** https://astrostretch-lab.streamlit.app

## Why I built it

When I first worked with raw telescope images, I was surprised by how little they resembled the finished astronomy images I was used to seeing. A FITS file could look almost completely dark even though faint structure was still present in the pixel data.

I built AstroStretch to understand that process instead of only moving sliders inside existing astronomy software.

## What it does

AstroStretch lets a user:

- Open a built-in sample image or upload a FITS file
- Compare the original image with a stretched version
- Switch between linear, logarithmic, and asinh stretching
- Adjust the black point and white point
- Control stretch strength
- View image dimensions, pixel statistics, and FITS metadata
- Inspect the image’s pixel-value histogram
- Download the displayed result as a PNG

The built-in sample is synthetic and is included so the app can be tested immediately.

## How it works

The app reads a two-dimensional image from a FITS file using Astropy.

It then uses percentile-based black and white points instead of relying only on the absolute minimum and maximum pixel values. This prevents a small number of unusually bright or faulty pixels from controlling the entire display range.

After scaling the image between 0 and 1, AstroStretch applies the selected brightness transformation:

- **Linear:** preserves equal brightness differences
- **Logarithmic:** strongly lifts faint values while compressing bright ones
- **Asinh:** reveals faint detail while keeping bright regions more controlled

The original FITS measurements are never changed.

## What I learned

My first approach simply displayed every value between the image’s minimum and maximum. It worked technically, but the result was poor because a few extreme pixels dominated the range.

Building the app helped me understand that astronomical image processing is not about creating detail that was not there. It is about choosing how existing measurements are displayed, while being careful not to exaggerate noise.

## Limitations

- AstroStretch currently supports two-dimensional grayscale FITS images
- It does not perform calibration, stacking, colour combination, or scientific measurement
- Aggressive settings may make background noise appear more prominent
- The downloaded PNG is intended for display, not scientific analysis

## Run locally

Clone the repository:

```bash
git clone https://github.com/Hussain1802/astrostretch.git
cd astrostretch