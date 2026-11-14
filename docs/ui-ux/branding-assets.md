# Haramaya University Branding Assets

## Asset sources and local copies

All source assets were retrieved from the official Haramaya University website
and are bundled locally so the application does not need to request images from
the public website at runtime.

| Local asset | Official source | Source details |
| --- | --- | --- |
| `frontend/public/assets/haramaya-university-logo.png` | <https://www.haramaya.edu.et/wp-content/uploads/2026/03/cropped-hu1log.png> | Official transparent PNG wordmark, 567 x 108 pixels. The image is kept in its original format and proportions. |
| `frontend/public/assets/haramaya-campus-background.jpg` | <https://www.haramaya.edu.et/wp-content/uploads/2019/12/main-campus-dorm-1.jpg> | Official university media-library photo titled "Haramaya University main Campus Dorms Photos". Resized proportionally to 1280 x 720 and JPEG re-encoded at quality 86 for web delivery. |
| `frontend/public/assets/haramaya-laboratory.jpg` | Original page URL: <https://haramaya.edu.et/cncs/wp-content/uploads/sites/8/2021/04/20180817_085747.jpg>; downloaded via the `www` URL in the page's `srcset`: <https://www.haramaya.edu.et/cncs/wp-content/uploads/sites/8/2021/04/20180817_085747.jpg> | Referenced by the official [Facilities page](https://www.haramaya.edu.et/cncs/research/facilities/) (page title: "Facilities"; source image title/alt: "Student Learning at Lab"). The original is 5312 x 2988; the local copy is 1600 x 900, JPEG re-encoded at quality 88. |
| `frontend/public/assets/favicon.png` | Derived from the official logo above | A square crop of the original logo's seal, resized to 96 x 96 pixels. No separate or reconstructed emblem was used. |

## Color treatment

The current university wordmark contains green (`#319A43`), blue (`#044694`),
and orange (`#FF8400`) pixels. The official site's inspected page background
and text were `#F4F6F8` and `#10241A`, respectively. The interface uses green
as its primary direction, deepens the sampled green for text and buttons, and
uses the sampled blue and orange sparingly as supporting colors. Existing
slate utility classes are mapped to green-tinted neutrals for consistency
across authenticated pages.

These values are sampled from the live logo and website; they are not a
confirmed Haramaya University brand standard. No official brand guide was
identified during this work.

## Usage and approval

The official site was the source for the images, but no asset-reuse license or
brand-use approval was identified. Confirm permission with the University
before distributing or deploying the branded application publicly. The
application must not be presented as institutionally approved solely because
it uses these assets.
