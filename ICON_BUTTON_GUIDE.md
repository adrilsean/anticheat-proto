# Icon Square Button Implementation Guide

## What Changed

I've added a new **`IconSquareButton`** class to replace the rounded bubble buttons in your teacher portal menu. These are square buttons (140x140px) with emoji icons on top and text below.

### Features:
- **Square shape** (not rounded)
- **Icon + Text layout** (icon on top, text below)
- **Hover effects** (color transitions on hover)
- **Consistent styling** (matches your NU_BLUE color scheme)

---

## Menu Options (Currently Configured)

| Button | Icon | Text |
|--------|------|------|
| Generate Exam | 📝 | Generate Exam |
| View Logs | 📊 | View Exam Logs |
| Create Class | 👥 | Create New Class |
| Manage Classes | ⚙️ | Manage Classes |

---

## Customization Options

### Change Icons
Edit the menu_options in `main_qt.py` → `show_teacher_page()` method:

```python
menu_options = [
    ("Generate\nExam", "📋", 150, "exam"),           # Change 📋 to any emoji
    ("View Exam\nLogs", "📈", 265, "logs"),          # Change 📈 to any emoji
    ("Create New\nClass", "🎓", 380, "create_class"), # Change 🎓 to any emoji
    ("Manage\nClasses", "🔧", 495, "manage_class")    # Change 🔧 to any emoji
]
```

### Suggested Emoji Combinations

**Academic Theme:**
- 📝 (📋, ✍️) - Generate Exam
- 📊 (📈, 📉) - View Logs
- 👥 (🎓, 👨‍🎓) - Create Class
- ⚙️ (🔧, ⚙️) - Manage Class

**Modern Minimal:**
- 📄 - Exam
- 📑 - Logs
- 👤 - Students
- ⚡ - Settings

**Colorful:**
- 🎯 - Exam
- 🔍 - Logs
- 🌟 - Class
- 💡 - Manage

---

## Button Size & Layout Options

To adjust button size, change the `size=140` parameter in IconSquareButton creation:

```python
btn = IconSquareButton(text, icon_char=icon, parent=self, color=NU_BLUE, size=140)
```

Current layout (900px width):
- Button size: 140×140px
- Left margin: 380px (centers button)
- Vertical spacing: 115px between buttons

---

## Colors

### Theme Colors Available:
- `NU_BLUE` (#0B2C5D) - Main color (default)
- Custom colors - Pass any hex color code

Example with custom color:
```python
btn = IconSquareButton("Custom", "🎨", parent=self, color="#FF6B6B", size=140)
```

---

## Button Customization

Full IconSquareButton signature:
```python
IconSquareButton(
    text,                    # Button label text
    icon_char="📋",          # Emoji icon
    parent=None,             # Parent widget
    color=NU_BLUE,           # Background color (hex)
    text_color="white",      # Text color (hex)
    size=120                 # Button size in pixels (width & height)
)
```

---

## If You Want Static Icons Instead of Emojis

For using actual image files instead of emojis, modify the IconSquareButton class:

```python
def setButtonIcon(self, icon_path):
    """Load icon from file (PNG, JPG, SVG)"""
    icon = QIcon(icon_path)
    self.setIcon(icon)
    self.setIconSize(QSize(64, 64))
```

Create icons folder and use:
```python
btn.setButtonIcon("icons/exam.png")
```

---

## Layout Adjustment Example

If you want 2x2 grid instead of vertical list:

```python
menu_options = [
    ("Generate\nExam", "📝", 150, 150, "exam"),
    ("View Exam\nLogs", "📊", 550, 150, "logs"),
    ("Create New\nClass", "👥", 150, 350, "create_class"),
    ("Manage\nClasses", "⚙️", 550, 350, "manage_class")
]

for text, icon, x, y, key in menu_options:
    btn = IconSquareButton(text, icon_char=icon, parent=self, color=NU_BLUE, size=140)
    btn.setGeometry(x, y, 140, 140)
    btn.clicked.connect(lambda ch, k=key: self.launch_teacher(k))
    btn.show()
```

---

## Files Modified

1. **teacher_qt.py** - Added `IconSquareButton` class (lines ~141-189)
2. **main_qt.py** - Updated `show_teacher_page()` to use new buttons
3. **main_qt.py** - Updated imports to include `IconSquareButton`

---

## Quick Testing

Simply run `python main_qt.py` and navigate to TEACHER PORTAL to see the new square icon buttons!
