import os
import tkinter as tk

def throttled_resize(app, event):
        """
        Handles the main window resize event with debounce, only updating layout on column breakpoint change.
        """
        if event.widget == app.master:
            new_width = app.master.winfo_width()
            new_height = app.master.winfo_height()
            if (new_width != app.last_width) or (new_height != app.last_height):
                app.last_width = new_width
                app.last_height = new_height
                # Pause loading during resize
                app.pause_loading = True
                # Cancel any existing debounce timer
                if app.resize_timer is not None:
                    app.master.after_cancel(app.resize_timer)
                    app.resize_timer = None
                # Set a new debounce timer (e.g., 300ms)
                debounce_delay = 1000  # milliseconds
                app.resize_timer = app.master.after(debounce_delay, lambda: on_resize_complete(app))


def on_resize_complete(app):
        """
        Callback function triggered after debounce for main window resize.
        Updates the grid layout only if the number of columns needs to change.
        """
        canvas_width = app.canvas.winfo_width() - 60 # Adjust for margins
        if canvas_width <= 0:
            return # Avoid calculations with non-positive width

        potential_columns = app.calculate_columns_for_width(canvas_width)
        if app.columns is None or potential_columns != app.columns: # Check if app.columns is None for initial setup
            app.columns = potential_columns # Update column count
            app.update_grid_layout()
        # Resume loading after layout check (or update)
        app.pause_loading = False
        app.resize_timer = None


# ------------------------------------------------------------
# Mouse Wheel
# ------------------------------------------------------------
def on_mousewheel_main(app, event):
    app.on_mousewheel_event()  # Pause loading on mouse wheel

    # --- NEW: Set scrolling flag to True ---
    app.is_scrolling_main_grid = True

    if os.name == 'nt':
        delta = int(-1 * (event.delta / 120))
    else:
        delta = int(-1 * (event.delta))
    # --- MODIFIED: Initiate smooth scroll animation ---
    app.start_smooth_scroll_main(delta) # Call smooth scroll function instead of direct scroll #disabled smooth scrolling
    #app.canvas.yview_scroll(delta, "units")  # For main grid



    # --- NEW: Start or Reset Debounce Timer ---
    app.start_scroll_debounce_timer_main_grid()
        
        
def on_mousewheel_details(app, event, canvas_sub):
    app.on_mousewheel_event()  # Pause loading on mouse wheel
    if canvas_sub.winfo_exists():
        if os.name == 'nt':
            delta = int(-1 * (event.delta / 120))
        else:
            delta = int(-1 * (event.delta))
        # --- MODIFIED: Initiate smooth scroll animation for details ---
        app.start_smooth_scroll_details(delta, canvas_sub) # Call smooth scroll for details #disabled smooth scrolling
        #canvas_sub.yview_scroll(delta, "units") # For details grid


def ease_out_quintic_modified_speed(t, speed_factor=1.0):
        """Quintic ease-out function with speed control (for softer stop)."""
        modified_t = t * speed_factor  # Scale time by speed factor
        modified_t = min(modified_t, 1.0) # Ensure t doesn't exceed 1.0 after scaling
        t = modified_t - 1
        return t**9 + 1 # Using t**9 for quintic ease-out

def start_scroll_debounce_timer_main_grid(app):
    """Starts or resets the debounce timer for main grid scroll."""
    if app.scroll_debounce_timer_id:
        app.master.after_cancel(app.scroll_debounce_timer_id) # Cancel existing timer

    app.scroll_debounce_timer_id = app.master.after(
        app.scroll_debounce_delay,
        lambda: on_scroll_debounce_complete_main_grid(app) # Callback when timer finishes
    )

import tkinter as tk

def on_scroll_debounce_complete_main_grid(app):
    """Callback function when main grid scroll debounce timer completes.
    Checks mouse position and triggers hover effects conditionally based on widget type.
    Modified to leave image background color alone if it's already "red".
    """
    app.is_scrolling_main_grid = False  # Reset scrolling flag to False
    app.scroll_debounce_timer_id = None  # Clear timer ID
    print("Main Grid Scroll Debounce Complete - Hovers Re-enabled - Checking Mouse Position...")  # Debug print

    # --- NEW: Check mouse position and widget ---
    mouse_x, mouse_y = app.master.winfo_pointerxy()
    widget_under_mouse = app.master.winfo_containing(mouse_x, mouse_y)

    if widget_under_mouse:  # If mouse is over *some* widget in our app
        item_frame = None
        is_button = False  # Flag to track if mouse is over a Button (no longer relevant for image)
        is_label_img = False # Flag for image label
        is_label_info = False # Flag for info label


        if isinstance(widget_under_mouse, tk.Button):  # If it's a Button (likely not image button anymore in main grid, maybe other buttons in your UI)
            item_frame = widget_under_mouse.master
            is_button = True  # Set Button flag (might be other buttons in your UI)
            #print("Mouse is over a Button (tk.Button - check if expected in main grid)")  # Debug - check if this is expected in main grid
        elif isinstance(widget_under_mouse, tk.Label):  # If it's a Label (could be image or info label)
            item_frame = widget_under_mouse.master
            if widget_under_mouse == item_frame.winfo_children()[0]: # Assuming image label is the first child
                is_label_img = True # It's the image label
                #print("Mouse is over an Image Label (tk.Label for image)")
            elif widget_under_mouse == item_frame.winfo_children()[1]: # Assuming info label is the second child
                is_label_info = True # It's the info label
                #print("Mouse is over an Info Label (tk.Label for text)")
            else:
                pass
                #print("Mouse is over a Label (tk.Label - but not recognized as image or info label)") # Debug - unexpected label?

        else:
            #print("Mouse is over neither Button nor Label (in main grid items)")  # Debug
            item_frame = None

        if item_frame and app.is_descendant_of(item_frame, app.scrollable_frame):  # Check if part of main grid
            #print("Mouse is over a main grid item (descendant of scrollable_frame)")  # Debug

            # --- NEW: Trigger sidebar update ALWAYS if mouse is over a main grid item (Image Label or Info Label) ---
            pil_image, info_data, picture_path, zip_file, folder_name, spawn_cmd, img_label_widget, info_label_widget = item_frame.item_data_tuple  # Get stored data (now with labels)
            app.show_main_sidebar_info(info_data, picture_path, zip_file, folder_name, item=(picture_path, spawn_cmd, zip_file, info_data, folder_name))  # Call sidebar update
            print("Sidebar updated (triggered by debounce complete)")  # Debug

            # --- MODIFIED Highlight Logic: Trigger background change for IMAGE LABEL (lbl_img) ---
            if is_label_img: # Check if mouse is over the image label
                #print("Mouse is over an IMAGE LABEL - Triggering background change...") # Debug

                # --- CONDITION ADDED HERE: Check if current bg color is NOT "red" ---
                current_bg_color = img_label_widget.cget('bg') # Get current background color
                if current_bg_color != "red": # Check if it's NOT "red"
                    hover_bg_color = app.global_highlight_color # Define hover background color here (or get from a setting)
                    img_label_widget.config(bg=hover_bg_color) # Change background of image label
                    print("Image Label background change triggered (triggered by debounce complete)") # Debug
                else:
                    print("Image Label background is 'red', leaving it alone (triggered by debounce complete)")
                    pass # Leave the color as 'red'
                # --- CONDITION ADDED HERE: Check if current bg color is NOT "red" ---
            else:
                pass
                #print("Mouse is NOT over an IMAGE LABEL - Background change NOT triggered.") # Debug
            # --- MODIFIED Highlight Logic: Trigger background change for IMAGE LABEL (lbl_img) ---


            return  # Exit after triggering hover effects

    else:
        print("Mouse is not over any widget in the app window.") # Debug - Mouse not over app window

    #print("Mouse is NOT over a main grid item, or item not found. No hover effects triggered on debounce complete.")  # Debug print - if no hover triggered
    #print("--- on_scroll_debounce_complete_main_grid() - DEBUG OUTPUT END ---\n")  # Debug end marker
        
def is_descendant_of(app, widget, ancestor):
        """Checks if 'widget' is a descendant of 'ancestor' in Tkinter hierarchy."""
        parent = widget.master
        while parent:
            if parent == ancestor:
                return True
            parent = parent.master
        return False
        
def start_smooth_scroll_main(app, delta_units):
    """Starts smooth scrolling animation for the main canvas - NORMALIZED SPEED."""
    if app.scroll_animation_timer:
        app.master.after_cancel(app.scroll_animation_timer)  # Cancel any existing animation

    app.scroll_delta_units = delta_units  # Store delta in UNITS

    current_yview = app.canvas.yview()  # Get current yview
    current_pos = current_yview[0]  # Get the current top position (0.0 to 1.0)

    canvas_height = app.canvas.winfo_height()
    scrollable_height = app.canvas.bbox("all")[3] if app.canvas.bbox("all") else canvas_height # Use canvas height as fallback
    if scrollable_height <= 0:
        scrollable_height = canvas_height # Prevent division by zero

    # --- NEW: Calculate scroll step based on item height and canvas size ---
    estimated_item_height = 160  # Estimate item height in pixels (image + label + padding) - ADJUST IF NEEDED
    items_visible_in_viewport = canvas_height / estimated_item_height
    scroll_units_per_item = items_visible_in_viewport / (scrollable_height / estimated_item_height) if scrollable_height > 0 else 0.1 # Fallback if scrollable_height is 0

    scroll_step_units = scroll_units_per_item * 0.35 # Adjust multiplier (1.5) for overall speed - HIGHER = FASTER
    target_pos_units = current_pos + (delta_units * scroll_step_units)
    target_pos_units = max(0.0, min(1.0, target_pos_units))  # Clamp between 0.0 and 1.0

    app.scroll_current_yview = current_pos
    app.scroll_target_yview = target_pos_units
    animate_scroll_main(app, 0)  # Start animation from step 0


def start_smooth_scroll_details(app, delta_units, canvas_sub):
    """Starts smooth scrolling animation for the details canvas - NORMALIZED SPEED."""
    if app.scroll_animation_timer:
        app.details_window.after_cancel(app.scroll_animation_timer)  # Cancel existing details animation

    app.scroll_delta_units = delta_units  # Store delta in UNITS

    current_yview = canvas_sub.yview()  # Get current yview
    current_pos = current_yview[0]  # Get the current top position (0.0 to 1.0)

    canvas_height = canvas_sub.winfo_height()
    scrollable_height = canvas_sub.bbox("all")[3] if canvas_sub.bbox("all") else canvas_height # Use canvas height as fallback
    if scrollable_height <= 0:
        scrollable_height = canvas_height # Prevent division by zero


    # --- NEW: Calculate scroll step based on item height and canvas size ---
    estimated_item_height = 140  # Estimate item height in pixels for details - ADJUST IF NEEDED
    items_visible_in_viewport = canvas_height / estimated_item_height
    scroll_units_per_item = items_visible_in_viewport / (scrollable_height / estimated_item_height) if scrollable_height > 0 else 0.1 # Fallback if scrollable_height is 0

    scroll_step_units = scroll_units_per_item * 0.35 # Adjust multiplier (1.5) for overall speed - HIGHER = FASTER
    target_pos_units = current_pos + (delta_units * scroll_step_units)
    target_pos_units = max(0.0, min(1.0, target_pos_units))  # Clamp between 0.0 and 1.0

    app.scroll_current_yview = current_pos
    app.scroll_target_yview = target_pos_units
    animate_scroll_details(app, 0, canvas_sub)  # Start details animation from step 0

def animate_scroll_main(app, step):
    """Animates smooth scrolling for the main canvas - ENSURE FULL EASING."""
    if step > app.scroll_animation_steps:
        app.canvas.yview_moveto(app.scroll_target_yview) # Final position - ensure target is reached exactly
        app.scroll_animation_timer = None  # Animation finished
        return

    easing_factor = ease_out_quintic_modified_speed(step / app.scroll_animation_steps, speed_factor=1.8)
    new_yview = app.scroll_current_yview + (app.scroll_target_yview - app.scroll_current_yview) * easing_factor

    # --- MODIFIED: Always set yview, even if close to target ---
    app.canvas.yview_moveto(new_yview)
    


    app.scroll_animation_timer = app.master.after(
        app.scroll_animation_duration // app.scroll_animation_steps,
        lambda: animate_scroll_main(app, step + 1)
    )

def animate_scroll_details(app, step, canvas_sub):
    """Animates smooth scrolling for the details canvas - ENSURE FULL EASING."""
    if step > app.scroll_animation_steps:
        canvas_sub.yview_moveto(app.scroll_target_yview) # Final position - ensure target is reached exactly
        app.scroll_animation_timer = None  # Animation finished
        return

    easing_factor = ease_out_quintic_modified_speed(step / app.scroll_animation_steps, speed_factor=1.8)
    new_yview = app.scroll_current_yview + (app.scroll_target_yview - app.scroll_current_yview) * easing_factor
    canvas_sub.yview_moveto(new_yview) # Always set yview

    app.scroll_animation_timer = app.details_window.after(
        app.scroll_animation_duration // app.scroll_animation_steps,
        lambda: animate_scroll_details(app, step + 1, canvas_sub)
    )


        
#-----------------------------------------


def calculate_columns_for_width(app, width, is_details=False): #using the window widh
    """
    Given the window width, determine how many columns can fit and calculate dynamic horizontal padding.
    """
    image_width = 252
    min_padding = 1  # Minimum spacing between images

    # Get window width directly from app master
    
    if not is_details:
        width = app.master.winfo_width()
    else:
        width = app.details_window.winfo_width()

    # Subtract sidebar width (270 pixels) from available width for layout calculations
    layout_width = max(1, width - 338)

    max_possible_columns = layout_width // image_width
    num_columns = 1
    for n in range(max_possible_columns, 0, -1):
        # The required width: n images and n+1 gaps (edges and between images)
        required_width = n * image_width + (n + 1) * min_padding
        if layout_width >= required_width:
            num_columns = n
            break

    total_free_space = layout_width - (num_columns * image_width)
    h_padding = total_free_space / (num_columns + 1)
    # Guarantee that the padding is at least the minimum
    h_padding = max(h_padding, min_padding)


    width_based_subtraction = width / 5000

    h_padding = h_padding / 2
    
    h_padding -= width_based_subtraction

    print(f"{app.master.winfo_width()}x{app.master.winfo_height()}")

    print(f"DEBUG: [calculate_columns_for_width] - START Function Execution") # <-- ADD THIS LINE - START
    print(f"DEBUG: calculate_columns_for_width - width: {width}, layout_width: {layout_width}") # DEBUG
    print(f"DEBUG: calculate_columns_for_width - max_possible_columns: {max_possible_columns}") # <-- ADD THIS LINE - max_possible_columns
    print(f"DEBUG: calculate_columns_for_width - total_free_space: {total_free_space}")
    print(f"DEBUG: calculate_columns_for_width - num_columns (before return): {num_columns}") # <-- ADD THIS LINE - num_columns before return
    print(f"DEBUG: calculate_columns_for_width - h_padding (before return): {h_padding}") # <-- ADD THIS LINE - h_padding before return
    print(f"DEBUG: calculate_columns_for_width - return type: {type((num_columns, h_padding))}") # DEBUG
    print(f"DEBUG: calculate_columns_for_width - width_based_subtraction (before return): {width_based_subtraction}")
    print(f"DEBUG: [calculate_columns_for_width] - END Function Execution - About to RETURN") # <-- ADD THIS LINE - END

    return num_columns, h_padding
    
    
    

#-----------------------------------------

def animate_scroll_search_results(app, step, canvas_sub):
    """Animates smooth scrolling for the search results canvas - ENSURE FULL EASING."""
    if step > app.scroll_animation_steps:
        canvas_sub.yview_moveto(app.scroll_target_yview) # Final position - ensure target is reached exactly
        app.scroll_animation_timer = None  # Animation finished
        return

    easing_factor = ease_out_quintic_modified_speed(step / app.scroll_animation_steps, speed_factor=1.8)
    new_yview = app.scroll_current_yview + (app.scroll_target_yview - app.scroll_current_yview) * easing_factor
    canvas_sub.yview_moveto(new_yview) # Always set yview

    app.scroll_animation_timer = app.search_results_window.after(
        app.scroll_animation_duration // app.scroll_animation_steps,
        lambda: animate_scroll_search_results(app, step + 1, canvas_sub)
    )
    