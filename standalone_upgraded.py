import markdown
import re
from pathlib import Path

INPUT_FILE = "slides.md"
OUTPUT_FILE = "presentation.html"

# Template parts
TEMPLATE_HEAD = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Enhanced Presentation</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
    rel="stylesheet"
  />
  <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
  <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
  <style>
    body {
      background: #f8f9fa;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      transition: background 0.5s, color 0.5s;
    }
    .slide {
      display: none;
      padding: 2rem;
      border-radius: 1rem;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
      margin-bottom: 2rem;
      overflow: hidden;
      transition: background-color 0.7s ease;
      color: #212529;
    }
    .slide.active {
      display: flex;
      animation: fadeInSlide 0.7s ease forwards;
    }
    .slide-content {
      display: flex;
      flex-grow: 1;
      gap: 1rem;
      width: 100%;
    }
    .slide-part {
      flex-grow: 1;
      overflow-y: auto;
      border-radius: 0.5rem;
      padding: 1rem;
      background: #fff;
      border: 1px solid #ddd;
      box-sizing: border-box;
    }
    /* Slide transitions */
    @keyframes fadeInSlide {
      from { opacity: 0; transform: translateX(30px);}
      to { opacity: 1; transform: translateX(0);}
    }
    /* Dark theme */
    body.dark-theme {
      background: #121212;
      color: #eee;
    }
    body.dark-theme .slide-part {
      background: #1e1e1e;
      border-color: #333;
      color: #eee;
    }
    /* Pagination */
    .pagination-controls .btn {
      cursor: pointer;
    }
    /* Media embeds */
    video, audio {
      max-width: 100%;
      border-radius: 0.3rem;
      margin-top: 0.5rem;
    }
    /* Theme toggle */
    #theme-toggle {
      position: fixed;
      top: 1rem;
      right: 1rem;
      z-index: 9999;
    }
  </style>
</head>
<body>
  <button id="theme-toggle" class="btn btn-outline-secondary btn-sm">Toggle Theme</button>
  <div class="container my-4">
"""

TEMPLATE_FOOT = """
    <div class="d-flex justify-content-between mt-3">
      <button class="btn btn-primary" id="prev-slide">Previous</button>
      <button class="btn btn-primary" id="next-slide">Next</button>
    </div> <p align="center">Presented by: <b> <i>Nishan Lamichhane</i></b></p>
    <div class="pagination-controls text-center mt-3 mb-5">
"""

TEMPLATE_SCRIPT = """
    </div>
  </div>

  <script>
    let currentSlide = 0;
    const slides = $('.slide');
    const totalSlides = slides.length;
    let autoplayTimer = null;
    const autoplayDelay = 5000; // 5 seconds

    function showSlide(n, animType='fade') {
      if (n < 0 || n >= totalSlides) return;
      const $oldSlide = slides.eq(currentSlide);
      const $newSlide = slides.eq(n);

      // Animate out old slide
      $oldSlide.removeClass('active');

      // Animate in new slide
      $newSlide.addClass('active');

      $('.pagination-btn').removeClass('btn-primary').addClass('btn-outline-dark');
      $('.pagination-btn[data-index="' + n + '"]').removeClass('btn-outline-dark').addClass('btn-primary');
      currentSlide = n;
    }

    $('#prev-slide').click(() => {
      showSlide(currentSlide - 1);
      //resetAutoplay();
    });

    $('#next-slide').click(() => {
      showSlide(currentSlide + 1);
      //resetAutoplay();
    });

    $('.pagination-btn').click(function () {
      const index = parseInt($(this).attr('data-index'));
      showSlide(index);
      //resetAutoplay();
    });

    // Theme toggle
    $('#theme-toggle').click(() => {
      $('body').toggleClass('dark-theme');
    });

    // Autoplay
    function startAutoplay() {
      if (autoplayTimer) return;
      autoplayTimer = setInterval(() => {
        let next = currentSlide + 1;
        if(next >= totalSlides) next = 0;
        showSlide(next);
      }, autoplayDelay);
    }

    function resetAutoplay() {
      if (autoplayTimer) {
        clearInterval(autoplayTimer);
        autoplayTimer = null;
      }
      //startAutoplay();
    }

    // Export PDF
    $('#export-pdf').click(() => {
      const { jsPDF } = window.jspdf;
      const pdf = new jsPDF();
      let promises = [];
      slides.each(function(index) {
        const slide = this;
        promises.push(html2canvas(slide).then(canvas => {
          if(index > 0) pdf.addPage();
          const imgData = canvas.toDataURL('image/png');
          const imgProps = pdf.getImageProperties(imgData);
          const pdfWidth = pdf.internal.pageSize.getWidth();
          const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
          pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
        }));
      });
      Promise.all(promises).then(() => {
        pdf.save('presentation.pdf');
      });
    });

    // Export PNG images (one per slide)
    $('#export-png').click(() => {
      slides.each(function(index) {
        html2canvas(this).then(canvas => {
          const a = document.createElement('a');
          a.href = canvas.toDataURL('image/png');
          a.download = 'slide-' + (index + 1) + '.png';
          a.click();
        });
      });
    });

    
$(document).on('keydown', function(e) {
  if (e.key === 'ArrowRight') $('#next-slide').click();
  if (e.key === 'ArrowLeft') $('#prev-slide').click();
});

    // Start on first slide + autoplay
    $(document).ready(() => {
      showSlide(0);
      startAutoplay();

      // Pause autoplay on hover
      $('.slide').hover(() => {
        if(autoplayTimer) clearInterval(autoplayTimer);
        autoplayTimer = null;
      }, () => {
        startAutoplay();
      });
    });
  </script>
</body>
</html>
"""

def parse_markdown_slides(md_text):
    """
    Parses markdown text into slides.
    Each slide starts with:
    <!-- Slide N | columns=X | bg=#color | animation=fade -->
    Then slide content parts are separated by `---` lines.
    Returns list of dicts: [{columns, bg, animation, parts[]}, ...]
    """
    slides = []
    current_slide = None

    slide_start_re = re.compile(
        r"<!--\s*Slide\s*(\d+)?\s*\|\s*columns=(\d+)(?:\s*\|\s*bg=([#a-zA-Z0-9]+))?(?:\s*\|\s*animation=([a-zA-Z]+))?\s*-->"
    )

    parts = []

    lines = md_text.splitlines()
    for line in lines:
        m = slide_start_re.match(line.strip())
        if m:
            # Save old slide
            if current_slide is not None:
                current_slide['parts'] = parts
                slides.append(current_slide)
            # Start new slide
            slide_num = int(m.group(1)) if m.group(1) else len(slides)+1
            cols = int(m.group(2))
            bg = m.group(3) if m.group(3) else None
            anim = m.group(4) if m.group(4) else 'fade'
            current_slide = {'number': slide_num, 'columns': cols, 'bg': bg, 'animation': anim}
            parts = []
        elif line.strip() == '---':
            parts.append("__SPLIT__")
        else:
            if parts:
                if parts[-1] == "__SPLIT__":
                    parts.append(line)
                else:
                    parts[-1] += "\n" + line
            else:
                parts.append(line)
    # Add last slide
    if current_slide is not None:
        current_slide['parts'] = parts
        slides.append(current_slide)
    return slides

def render_slide_html(slide, idx):
    """Render a single slide with columns and background etc."""
    cols = slide['columns']
    parts = slide['parts']
    bg = slide.get('bg')
    anim = slide.get('animation', 'fade')

    # Split parts by __SPLIT__
    content_parts = []
    current = []
    for p in parts:
        if p == "__SPLIT__":
            content_parts.append('\n'.join(current).strip())
            current = []
        else:
            current.append(p)
    if current:
        content_parts.append('\n'.join(current).strip())

    # Markdown convert each part to HTML
    md_html_parts = []
    for part in content_parts:
        # Allow embedded HTML by enabling extensions
        md_html_parts.append(markdown.markdown(part, extensions=['fenced_code', 'codehilite', 'tables', 'toc', 'nl2br']))

    # Divide parts into columns, equally or by content count
    # If fewer parts than columns, fill empty columns
    col_count = cols
    while len(md_html_parts) < col_count:
        md_html_parts.append("")

    # Each part wrapped in div.slide-part
    parts_html = ''
    for cidx in range(col_count):
        parts_html += f'<div class="slide-part col">{md_html_parts[cidx]}</div>'

    style = ""
    if bg:
        if bg.startswith("url("):
            style += f"background-image:{bg}; background-size:cover;"
        else:
            style += f"background:{bg};"

    slide_html = f'''
    <section class="slide row justify-content-center align-items-stretch" id="slide-{idx}" style="{style}" data-animation="{anim}">
      <div class="slide-content row gx-3" style="width:100%;">
        {parts_html}
      </div>
    </section>
    '''
    return slide_html

def build_presentation():
    md_text = Path(INPUT_FILE).read_text(encoding="utf-8")
    slides = parse_markdown_slides(md_text)

    # Pagination buttons html
    pagination_html = ""
    for i in range(len(slides)):
        pagination_html += f'<button class="btn btn-outline-dark pagination-btn mx-1" data-index="{i}">{i+1}</button>'

    slides_html = "\n".join(render_slide_html(s, i) for i, s in enumerate(slides))

    full_html = (
        TEMPLATE_HEAD
        + slides_html
        + TEMPLATE_FOOT
        + pagination_html
        + """
        <div class="d-flex justify-content-center mb-5">
          <button class="btn btn-success mx-2" id="export-pdf">Export PDF</button>
          <button class="btn btn-success mx-2" id="export-png">Export PNGs</button>
        </div>
        """
        + TEMPLATE_SCRIPT
    )

    Path(OUTPUT_FILE).write_text(full_html, encoding="utf-8")
    print(f"Presentation generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    build_presentation()
