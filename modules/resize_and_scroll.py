import os
import tkinter as tk
import inspect 


def throttled_resize(app, event):
    """
    Handles the main window resize event with debounce, only updating layout on column breakpoint change.
    """

    if event.widget == app.master:
        new_width = app.master.winfo_width()
        new_height = app.master.winfo_height()
        if (new_width != app.last_width) or (new_height != app.last_height):
            
            app.resizing_window = True
            app.window_was_resized = True
            app.window_was_resized_2 = True
            



            
            if app.search_results_window_on_screen:
                print(f"if app.search_results_window_on_screen is true, temporarily destroying search results window with  app.search_results_window.destroy()")
                app.search_results_window.destroy()
            

            app.hide_main_grid_and_sidebar_start_passed += 1 # Set the flag for subsequent calls

            app.hide_main_grid_and_sidebar()
            print("DEBUG: hide_main_grid_and_sidebar called")

            if (hasattr(app, 'details_window') and      # Condition 1
                app.details_window is not None and      # Condition 2
                app.details_window.winfo_exists() and   # Condition 3
                app.details_window.wm_state() != 'withdrawn'): # Condition 4
                    # This block only runs if ALL conditions are True
                    try:
                        app.details_window.withdraw()
                        print("DEBUG: details_window.withdraw() called")
                    except tk.TclError as e:
                        print(f"Error withdrawing details window: {e}")
                    app.details_page_before_resize = getattr(app, 'details_page', 0)
                    print(f"DEBUG: Storing details page before resize: {app.details_page_before_resize}")


            #app.text_to_switch_back_to = app.new_button_label

            #if app.switch_to_beamng_button:
            #    app.switch_to_beamng_button.config(
            #        text=f"Resizing window to {new_height}x{new_width}",
            #        fg=app.global_highlight_color
            #    )
            
            app.no_configs_label.config(text=f"Adjusting window size... ({new_height}x{new_width})") # Set text
            app.no_configs_label.pack(side="left", padx=(10, 10)) # Make label visible


            # Determine the available width for images
            app.canvas.update_idletasks()
            width = app.canvas.winfo_width() - 60
            if app.columns is None:
                app.columns, app.column_padding = app.calculate_columns_for_width(width)
            else:
                _, app.column_padding = app.calculate_columns_for_width(width)



        print("Size changed to:", new_width, new_height)
        app.last_width = new_width
        app.last_height = new_height
        # Pause loading during resize
        app.pause_loading = True
        # Cancel any existing debounce timer
        if app.resize_timer is not None:
            app.master.after_cancel(app.resize_timer)
            app.resize_timer = None
        # Set a new debounce timer (e.g., 300ms)
        debounce_delay = 2000  # milliseconds
        app.resize_timer = app.master.after(debounce_delay, lambda: on_resize_complete(app))

        app.on_resize_complete_called += 1  # Increment the call count


def on_resize_complete(app):
    """
    Callback function triggered after debounce.
    MODIFIED: Only performs actions if a resize actually occurred.
    """
    print("\n--- DEBUG: on_resize_complete triggered ---")
    # Always clear the timer ID, regardless of resize or move
    app.resize_timer = None
    
    app.hide_no_configs_label()
    
    
    # --- ADDED CHECK ---
    # Only proceed with layout updates and state restoration IF the flag
    # indicates a size change happened during the sequence of events.
    if app.window_was_resized:
        print("DEBUG: Actual resize detected (window_was_resized=True). Performing actions.")

        # --- Start of Original on_resize_complete Logic (Now Indented) ---
        canvas_width = app.canvas.winfo_width() - 60 # Adjust for margins
        if canvas_width <= 0:
             print("DEBUG: Canvas width invalid, aborting resize actions.") # Added log
             # Need to reset flags even if aborting here
             app.resizing_window = False
             app.pause_loading = False
             app.window_was_resized = False # Reset the flag
             app.window_was_resized_2 = False # Reset the flag
             return

        potential_columns = app.calculate_columns_for_width(canvas_width)
        app.columns = potential_columns # Update column count

        app.is_search_results_window_active_bypass_flag = True
        app.is_search_results_window_active = False

        app._track_normal_geometry()
        app.save_window_geometry()
        print("DEBUG: on_resize_complete - app._track_normal_geometry() and app.save_window_geometry() called")

        if app.search_results_window_on_screen:
            app.window_size_changed_during_search_results_window = True
            print("DEBUG - app.window_size_changed_during_search_results_window = True")
            if not app.details_window:
                app.search_results_window = app.show_search_results_window(app.data)
                print("DEBUG - recreating search results window because the details window is not open")
            else:
                print("DEBUG - not recreating search results window because details window is open, this should be handled in the on details window close function")
            print("DEBUG: on_resize_complete thinks the search result is active -  if app.search_results_window_on_screen: is true")
        else:
            print("DEBUG: on_resize_complete DOES NOT THINK the search result is active -  if app.search_results_window_on_screen: is False")

        if app.details_window: 
            app.window_size_changed_during_details_window = True
            print("DEBUG: on_resize_complete - app.details_window is not None, details window on screen, window_size_changed_during_details_window = True")
            try: # Minor safety addition
                app.details_window.deiconify()
                print("DEBUG: on_resize_complete - app.details_window.deiconify() called")
            except tk.TclError:
                print("DEBUG: Error during details_window.deiconify(), window might not exist.")


        #if app.switch_to_beamng_button:
        #     try: # Minor safety addition + avoid duplicate config
        #         app.switch_to_beamng_button.config(
        #             text=app.text_to_switch_back_to,
        #             fg="white"
        #         )
        #     except tk.TclError:
        #         print("DEBUG: Error configuring switch_to_beamng_button.")


        app.show_main_grid_and_sidebar() # Show the main grid and sidebar again
        print("DEBUG: show_main_grid_and_sidebar called after resize")

        if not app.details_window and not app.search_results_window_on_screen: 
            print("if not app.details_window and not app.search_results_window_on_screen: Condition met, calling update_grid_layout")
            app.update_grid_layout()

        # Reset flags specific to resize completion *inside* the 'if'
        app.resizing_window = False # Reset resizing state
        print("DEBUG: Resizing window completed, app.resizing_window = False")
        app.pause_loading = False # Resume loading
        print("DEBUG: Resuming loading")

        # *** IMPORTANT: Reset the flag that was checked ***
        app.window_was_resized = False
        app.window_was_resized_2 = False # Reset this too if it's used elsewhere

        # --- End of Original on_resize_complete Logic ---

    else:
        # --- ADDED ELSE BLOCK ---
        # This block runs if the timer fired, but no resize occurred (just a move)
        print("DEBUG: No resize detected (window_was_resized=False). Skipping layout actions.")
        # Ensure essential state flags are reset even after just a move
        app.resizing_window = False # Ensure this is false
        app.pause_loading = False   # Ensure loading is not paused

    print("--- END on_resize_complete ---")




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


    stack = inspect.stack()
    caller_function_name = "<unknown>"
    caller_filename = "<unknown>"
    caller_lineno = 0
    if len(stack) > 1:
        # stack[0] is the current frame (update_grid_layout)
        # stack[1] is the caller's frame
        caller_frame_record = stack[1]
        caller_function_name = caller_frame_record.function
        caller_filename = caller_frame_record.filename
        caller_lineno = caller_frame_record.lineno
        # You can even get the specific code line that made the call:
        caller_code_context = caller_frame_record.code_context
        print(f"    Code context: {caller_code_context}") # Might be None

    print(f"--- calculate_columns_for_width CALLED BY: {caller_function_name} in {caller_filename} at line {caller_lineno} ---")


    image_width = 252
    min_padding = 1  # Minimum spacing between images

    # Get window width directly from app master
    
    if not is_details:
        print(f"function signature [[ def calculate_columns_for_width(app, width, is_details=False): ]] - is_details is false")
        width = app.master.winfo_width()
    else:
        print(f"function signature [[ def calculate_columns_for_width(app, width, is_details=False): ]] - is_details is true")
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
