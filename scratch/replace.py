import os

with open("frontend/src/style.css", "r") as f:
    css = f.read()

root_vars = """
:root, body.theme-normal {
  --primary-color: #10b981;
  --primary-light: #34d399;
  --primary-bg: rgba(16, 185, 129, 0.2);
  --primary-border: rgba(16, 185, 129, 0.5);
  --gradient-start: #06b6d4;
  --gradient-end: #10b981;
}

body.theme-visual {
  --primary-color: #f97316;
  --primary-light: #fdba74;
  --primary-bg: rgba(249, 115, 22, 0.2);
  --primary-border: rgba(249, 115, 22, 0.5);
  --gradient-start: #ef4444;
  --gradient-end: #f97316;
}

body.theme-video {
  --primary-color: #a855f7;
  --primary-light: #d8b4fe;
  --primary-bg: rgba(168, 85, 247, 0.2);
  --primary-border: rgba(168, 85, 247, 0.5);
  --gradient-start: #d946ef;
  --gradient-end: #a855f7;
}

body.theme-other {
  --primary-color: #3b82f6;
  --primary-light: #93c5fd;
  --primary-bg: rgba(59, 130, 246, 0.2);
  --primary-border: rgba(59, 130, 246, 0.5);
  --gradient-start: #0ea5e9;
  --gradient-end: #3b82f6;
}

"""

css = root_vars + css

# Replacements:
css = css.replace("rgba(16, 185, 129, 0.2)", "var(--primary-bg)")
css = css.replace("rgba(16, 185, 129, 0.5)", "var(--primary-border)")
css = css.replace("#10b981", "var(--primary-color)")
css = css.replace("#34d399", "var(--primary-light)")
css = css.replace("#06b6d4", "var(--gradient-start)")

# Fix the gradients where we already replaced 10b981 with var(--primary-color)
css = css.replace("var(--gradient-start), var(--primary-color)", "var(--gradient-start), var(--gradient-end)")

# Fix the mode select arrow color to white since SVG backgrounds don't inherit variables easily
css = css.replace("stroke='%23var(--primary-light)'", "stroke='%23ffffff'")

with open("frontend/src/style.css", "w") as f:
    f.write(css)

print("Replaced successfully")
