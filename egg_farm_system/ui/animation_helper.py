"""
Animation Helper Utility

Provides reusable animation methods for QWidgets using QPropertyAnimation.
Designed for high performance and stability (no simulation, error-free).
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QSize, QParallelAnimationGroup, QSequentialAnimationGroup, QAbstractAnimation, Qt, Slot
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect, QStackedWidget

class AnimationHelper:
    """Helper class for common widget animations."""

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300, start_opacity: float = 0.0, end_opacity: float = 1.0) -> QPropertyAnimation:
        """Fade in a widget."""
        if not widget:
            return None
        
        # Ensure widget has opacity effect
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        
        # Initial state
        widget.setVisible(True)
        effect.setOpacity(start_opacity)
        
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(start_opacity)
        anim.setEndValue(end_opacity)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Store animation on widget to prevent garbage collection
        if not hasattr(widget, "_active_animations"):
            widget._active_animations = []
        widget._active_animations.append(anim)
        
        # Cleanup on finish
        def cleanup():
            if hasattr(widget, "_active_animations") and anim in widget._active_animations:
                widget._active_animations.remove(anim)
                
        anim.finished.connect(cleanup)
        anim.start()
        return anim

    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300, hide_on_finish: bool = True) -> QPropertyAnimation:
        """Fade out a widget."""
        if not widget:
            return None

        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            effect.setOpacity(1.0)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(effect.opacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InCubic)

        if hide_on_finish:
            anim.finished.connect(widget.hide)
            
        # Store animation
        if not hasattr(widget, "_active_animations"):
            widget._active_animations = []
        widget._active_animations.append(anim)
        
        def cleanup():
             if hasattr(widget, "_active_animations") and anim in widget._active_animations:
                widget._active_animations.remove(anim)

        anim.finished.connect(cleanup)
        anim.start()
        return anim

    @staticmethod
    def slide_in(widget: QWidget, duration: int = 300, direction: str = "right", offset: int = 50) -> QPropertyAnimation:
        """Slide widget in from a direction (affects pos)."""
        if not widget:
            return None
            
        final_pos = widget.pos()
        start_pos = QPoint(final_pos)
        
        if direction == "right":
            start_pos.setX(final_pos.x() + offset)
        elif direction == "left":
            start_pos.setX(final_pos.x() - offset)
        elif direction == "up":
            start_pos.setY(final_pos.y() - offset)
        elif direction == "down":
            start_pos.setY(final_pos.y() + offset)

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(start_pos)
        anim.setEndValue(final_pos)
        anim.setEasingCurve(QEasingCurve.OutBack) # Bouncy feel
        
        widget.setVisible(True)
        anim.start()
        return anim

    @staticmethod
    def shake(widget: QWidget, duration: int = 500) -> QSequentialAnimationGroup:
        """Shake animation for error feedback."""
        if not widget:
            return None
            
        original_pos = widget.pos()
        x = original_pos.x()
        y = original_pos.y()
        offset = 5
        
        anim_group = QSequentialAnimationGroup(widget)
        
        for i in range(5):
            step_offset = offset - i # Diminishing shake
            p1 = QPoint(x + step_offset, y)
            p2 = QPoint(x - step_offset, y)
            
            anim1 = QPropertyAnimation(widget, b"pos")
            anim1.setDuration(duration // 10)
            anim1.setStartValue(p2 if i > 0 else original_pos)
            anim1.setEndValue(p1)
            
            anim2 = QPropertyAnimation(widget, b"pos")
            anim2.setDuration(duration // 10)
            anim2.setStartValue(p1)
            anim2.setEndValue(p2)
            
            anim_group.addAnimation(anim1)
            anim_group.addAnimation(anim2)
            
        # Return to original
        final_anim = QPropertyAnimation(widget, b"pos")
        final_anim.setDuration(duration // 10)
        final_anim.setStartValue(QPoint(x - (offset - 4), y)) # Approx last pos
        final_anim.setEndValue(original_pos)
        anim_group.addAnimation(final_anim)
        
        anim_group.start(QAbstractAnimation.DeleteWhenStopped)
        return anim_group
    
    @staticmethod
    def animate_stacked_widget_transition(stacked_widget: QStackedWidget, new_widget: QWidget, 
                                        direction: str = "right", duration: int = 300):
        """
        Animate transition between widgets in a QStackedWidget.
        This is a simulated slide effect since QStackedWidget doesn't support it natively easily without subclassing.
        However, a cross-fade is safer and cleaner for standard QStackedWidget.
        """
        if not stacked_widget or not new_widget:
            return

        # Add new widget if not present
        if stacked_widget.indexOf(new_widget) == -1:
            stacked_widget.addWidget(new_widget)
            
        # Get current widget
        current_widget = stacked_widget.currentWidget()
        
        if not current_widget:
            stacked_widget.setCurrentWidget(new_widget)
            return

        # Ensure new widget is visible and sized (for layout) but possibly 0 opacity initially
        stacked_widget.setCurrentWidget(new_widget)
        
        # Simple cross-fade implementation
        # Note: In standard QStackedWidget, only one widget is visible at a time.
        # So we can only animate the "in" of the new one, we can't cross-fade two active widgets easily
        # without painting them manually.
        # Strategy: Just fade in the new one.
        
        AnimationHelper.fade_in(new_widget, duration=duration, start_opacity=0.0)

    @staticmethod
    def count_up(label: QWidget, start_val: float, end_val: float, duration: int = 1000, 
                 is_int: bool = False, prefix: str = "", suffix: str = ""):
        """Animate a number counting up in a QLabel."""
        # This requires a custom property or a value changed signal.
        # Since QLabel doesn't have a numeric property, we can use a VariantAnimation
        # or just a QTimer for simplicity and control.
        from PySide6.QtCore import QVariantAnimation
        
        anim = QVariantAnimation(label)
        anim.setStartValue(start_val)
        anim.setEndValue(end_val)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.OutQuart)
        
        def update_text(value):
            if is_int:
                txt = f"{int(value):,}"
            else:
                txt = f"{value:,.2f}"
            label.setText(f"{prefix}{txt}{suffix}")
            
        anim.valueChanged.connect(update_text)
        anim.start(QAbstractAnimation.DeleteWhenStopped)
        return anim
