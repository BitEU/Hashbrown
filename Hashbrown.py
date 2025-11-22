import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import sys
import re
import tempfile
import threading
import json
import subprocess
from PIL import Image

try:
    # Try newer moviepy import structure (v2.x)
    from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, AudioClip
except ImportError:
    # Fall back to older import structure (v1.x)
    from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
    from moviepy.audio.AudioClip import AudioClip


class TimeInputField(ttk.Frame):
    """Custom time input field with HH:MM:SS format and auto-navigation"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.placeholders = {"hour": "hh", "min": "mm", "sec": "ss"}
        
        self.entries = []
        self.next_external_field = None  # For cross-TimeInputField navigation
        
        # Hour field
        self.hour_var = tk.StringVar()
        self.hour_entry = ttk.Entry(self, textvariable=self.hour_var, width=3, justify='center')
        self.hour_entry.pack(side=tk.LEFT)
        self.entries.append(self.hour_entry)
        
        ttk.Label(self, text=" : ").pack(side=tk.LEFT)
        
        # Minute field
        self.min_var = tk.StringVar()
        self.min_entry = ttk.Entry(self, textvariable=self.min_var, width=3, justify='center')
        self.min_entry.pack(side=tk.LEFT)
        self.entries.append(self.min_entry)
        
        ttk.Label(self, text=" : ").pack(side=tk.LEFT)
        
        # Second field
        self.sec_var = tk.StringVar()
        self.sec_entry = ttk.Entry(self, textvariable=self.sec_var, width=3, justify='center')
        self.sec_entry.pack(side=tk.LEFT)
        self.entries.append(self.sec_entry)
        
        # Bind events for auto-navigation
        self._setup_placeholders()
        self._setup_bindings()
    
    def _setup_placeholders(self):
        self._add_placeholder(self.hour_entry, self.placeholders["hour"])
        self._add_placeholder(self.min_entry, self.placeholders["min"])
        self._add_placeholder(self.sec_entry, self.placeholders["sec"])


    def _add_placeholder(self, entry, placeholder_text):
        entry.insert(0, placeholder_text)
        entry.config(foreground="grey")
        
        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.config(foreground="black")
                
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder_text)
                entry.config(foreground="grey")
        
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def set_next_field(self, entry_widget):
        """Set the next field to navigate to after the last entry"""
        self.next_external_field = entry_widget
    
    def _setup_bindings(self):
        """Setup key bindings for auto-navigation"""
        for i, entry in enumerate(self.entries):
            entry.bind('<KeyPress>', lambda e, idx=i: self._on_key_press(e, idx))
            entry.bind('<BackSpace>', lambda e, idx=i: self._on_backspace(e, idx))
            # Bind after the key is processed to handle auto-advance
            entry.bind('<KeyRelease>', lambda e, idx=i: self._on_key_release(e, idx))
    
    def _on_key_press(self, event, index):
        """Handle key press with auto-advance"""
        # Allow standard navigation keys (Tab, BackSpace, Arrows, Delete) to function normally
        if event.keysym in ('Tab', 'ISO_Left_Tab', 'BackSpace', 'Left', 'Right', 'Delete', 'Return'):
            return None

        # Only allow numbers
        if event.char and not event.char.isdigit():
            return 'break'
        
        entry = self.entries[index]
        current_value = entry.get()
        
        # If selecting text, allow overwrite
        if entry.selection_present():
            return None

        # Limit to 2 digits
        if len(current_value) >= 2:
            # If we already have 2 digits, move to next field and prevent this digit
            if index < len(self.entries) - 1:
                self.entries[index + 1].focus()
                self.entries[index + 1].icursor(0)
            elif self.next_external_field:
                self.next_external_field.focus()
                self.next_external_field.icursor(0)
            return 'break'
        
        # Allow the digit to be entered
        return None
    
    def _on_key_release(self, event, index):
        """Handle key release to auto-advance after entering second digit"""
        # Only process digit keys
        if not event.char.isdigit():
            return
        
        entry = self.entries[index]
        current_value = entry.get()
        
        # If we just filled this field with 2 digits, move to next
        if len(current_value) == 2:
            if index < len(self.entries) - 1:
                # Move to next field within this TimeInputField
                self.entries[index + 1].focus()
                self.entries[index + 1].icursor(0)
            elif self.next_external_field:
                # Move to external field (e.g., from Start SS to End HH)
                self.next_external_field.focus()
                self.next_external_field.icursor(0)
    
    def _on_backspace(self, event, index):
        """Handle backspace with auto-retreat"""
        entry = self.entries[index]
        
        # If field is empty or cursor at 0, move back
        if (not entry.get() or entry.index(tk.INSERT) == 0) and index > 0:
            self.entries[index - 1].focus()
            self.entries[index - 1].icursor(tk.END)
            return 'break'
        
        return None
    
    def get_value(self):
        """Get the time value in seconds"""
        try:
            h_str = self.hour_var.get()
            m_str = self.min_var.get()
            s_str = self.sec_var.get()

            # Handle placeholders
            if h_str == self.placeholders["hour"]: h_str = "0"
            if m_str == self.placeholders["min"]: m_str = "0"
            if s_str == self.placeholders["sec"]: s_str = "0"

            hours = int(h_str) if h_str.isdigit() else 0
            minutes = int(m_str) if m_str.isdigit() else 0
            seconds = int(s_str) if s_str.isdigit() else 0

            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return None
    
    def get_formatted_value(self):
        """Get the time value formatted as HH:MM:SS"""
        h = self.hour_var.get()
        m = self.min_var.get()
        s = self.sec_var.get()
        
        # Clean placeholders
        if h == self.placeholders["hour"]: h = "00"
        if m == self.placeholders["min"]: m = "00"
        if s == self.placeholders["sec"]: s = "00"
        
        return f"{h.zfill(2)}:{m.zfill(2)}:{s.zfill(2)}"
    
    def set_value(self, hours=0, minutes=0, seconds=0):
        """Set the time value"""
        self.hour_var.set(str(hours).zfill(2))
        self.min_var.set(str(minutes).zfill(2))
        self.sec_var.set(str(seconds).zfill(2))
        
        # Update colors since they are no longer placeholders
        for entry in self.entries:
            entry.config(foreground="black")

    def toggle_hour_field(self, show=True):
        # The separator label is the second widget created in __init__
        hour_separator = self.winfo_children()[1]
        
        if show:
            # Pack before the minute entry to ensure correct order (HH : MM)
            # We check if it's mapped to prevent redundant packing errors
            if not self.hour_entry.winfo_ismapped():
                self.hour_entry.pack(side=tk.LEFT, before=self.min_entry)
                hour_separator.pack(side=tk.LEFT, before=self.min_entry)
        else:
            self.hour_entry.pack_forget()
            hour_separator.pack_forget()


class SegmentRow(ttk.Frame):
    """A single segment row with start/end times and delete button"""
    
    def __init__(self, parent, segment_num, on_delete, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.segment_num = segment_num
        self.on_delete = on_delete
        
        # Segment label
        ttk.Label(self, text=f"{segment_num}:").pack(side=tk.LEFT, padx=5)
        
        # Start time
        ttk.Label(self, text="Start:").pack(side=tk.LEFT, padx=5)
        self.start_time = TimeInputField(self)
        self.start_time.pack(side=tk.LEFT, padx=5)
        
        # End time
        ttk.Label(self, text="End:").pack(side=tk.LEFT, padx=5)
        self.end_time = TimeInputField(self)
        self.end_time.pack(side=tk.LEFT, padx=5)
        
        # Duration label
        self.duration_label = ttk.Label(self, text="Duration: 00:00:00")
        self.duration_label.pack(side=tk.LEFT, padx=10)

        # Link the start and end time fields for navigation
        self.start_time.set_next_field(self.end_time.entries[0])
        
        # Delete button
        self.delete_btn = ttk.Button(self, text="✕", width=3, command=self._on_delete_click, style='Danger.TButton')
        self.delete_btn.pack(side=tk.LEFT, padx=5)
    
        self.start_time.hour_var.trace_add("write", self._update_duration)
        self.start_time.min_var.trace_add("write", self._update_duration)
        self.start_time.sec_var.trace_add("write", self._update_duration)
        self.end_time.hour_var.trace_add("write", self._update_duration)
        self.end_time.min_var.trace_add("write", self._update_duration)
        self.end_time.sec_var.trace_add("write", self._update_duration)

    def _update_duration(self, *args):
        start_sec = self.start_time.get_value()
        end_sec = self.end_time.get_value()

        if start_sec is not None and end_sec is not None and end_sec > start_sec:
            duration = end_sec - start_sec
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            self.duration_label.config(text=f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.duration_label.config(text="Duration: --:--:--")
    
    def _on_delete_click(self):
        """Handle delete button click"""
        if self.on_delete:
            self.on_delete(self)
    
    def get_segment(self):
        """Get segment start and end times in seconds"""
        start = self.start_time.get_value()
        end = self.end_time.get_value()
        return (start, end) if start is not None and end is not None else None
    
    def update_label(self, num):
        """Update segment number label"""
        self.segment_num = num
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Label) and widget.cget('text').startswith('Segment') or widget.cget('text').endswith(':'):
                 # Simple check for the first label "1:", "2:", etc.
                 if len(widget.cget('text')) < 5 and widget.cget('text').endswith(':'):
                    widget.config(text=f"{num}:")
                    break


class HashbrownApp(TkinterDnD.Tk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Configure ffmpeg path for moviepy
        self._configure_ffmpeg()
        
        self.title("Hashbrown")
        self.geometry("700x700") # Increased slightly to accommodate new checkbox
        
        # Set window icon
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png')
        if os.path.exists(logo_path):
            try:
                self.iconphoto(True, tk.PhotoImage(file=logo_path))
            except Exception:
                pass  # If logo fails to load as icon, continue without it
        
        self.video_path = None
        self.video_duration = None
        self.video_bitrate = None # Stores the original bitrate
        self.is_video_long = False
        self.segment_rows = []
        self.is_processing = False
        self.show_overlay_var = tk.BooleanVar(value=True) # Variable for overlay toggle
        
        self._create_widgets()
        self._setup_drag_drop()
    
    def _configure_ffmpeg(self):
        """Configure ffmpeg path - use imageio_ffmpeg which is bundled with moviepy"""
        try:
            import imageio_ffmpeg
            self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            os.environ['IMAGEIO_FFMPEG_EXE'] = self.ffmpeg_path
        except Exception as e:
            # Fallback to system ffmpeg if imageio_ffmpeg fails
            self.ffmpeg_path = 'ffmpeg'
            import warnings
            warnings.warn(f"Could not load imageio_ffmpeg ({e}). Using system FFmpeg if available.")
    
    def _create_widgets(self):
        """Create all GUI widgets"""
        # Add this styling section
        style = ttk.Style(self)
        # Configure a custom style for the delete button
        style.configure('Danger.TButton', foreground='red', font=('Arial', 10, 'bold'))

        # Title with logo
        title_frame = ttk.Frame(self)
        title_frame.pack(pady=10)
        
        # Load and display logo
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png')
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path)
                # Keep original size (64x43)
                self.logo_photo = tk.PhotoImage(file=logo_path)
                logo_label = ttk.Label(title_frame, image=self.logo_photo)
                logo_label.pack(side=tk.LEFT, padx=10)
            except Exception:
                pass  # If logo fails to load, just show text
        
        title_label = ttk.Label(title_frame, text="Hashbrown", font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # File upload section
        upload_frame = ttk.LabelFrame(self, text="Video File", padding=10)
        upload_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.file_label = ttk.Label(upload_frame, text="No file selected", foreground='gray')
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(upload_frame, text="Browse...", command=self._browse_file).pack(side=tk.RIGHT, padx=5)
        
        # Segments section
        segments_frame = ttk.LabelFrame(self, text="Redact Segments", padding=10)
        segments_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Scrollable frame for segments
        canvas = tk.Canvas(segments_frame, height=250)
        scrollbar = ttk.Scrollbar(segments_frame, orient="vertical", command=canvas.yview)
        self.segments_container = ttk.Frame(canvas)
        
        self.segments_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.segments_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add segment button
        ttk.Button(segments_frame, text="+", command=self._add_segment).pack(pady=10)
        
        # Add first segment by default
        self._add_segment()
        
        # Progress Section
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="0%", font=('Arial', 9))
        self.progress_label.pack()

        # Options Section
        options_frame = ttk.Frame(self)
        options_frame.pack(pady=5)
        
        self.overlay_check = ttk.Checkbutton(
            options_frame, 
            text="Include Overlay Image (Re-encodes video)", 
            variable=self.show_overlay_var
        )
        self.overlay_check.pack()
        
        # Process button
        process_btn = ttk.Button(self, text="Process Video", command=self._process_video, 
                                 style='Accent.TButton')
        process_btn.pack(pady=10)
        
        # Status label
        self.status_label = ttk.Label(self, text="", foreground='blue')
        self.status_label.pack(pady=5)
    
    def _setup_drag_drop(self):
        """Setup drag and drop functionality"""
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self._on_drop)
    
    def _on_drop(self, event):
        """Handle file drop"""
        # Get the file path from drop event
        file_path = event.data
        # Remove curly braces if present
        file_path = file_path.strip('{}')
        
        if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
            self._load_video(file_path)
        else:
            messagebox.showerror("Invalid File", "Please select a valid video file.")
    
    def _browse_file(self):
        """Open file dialog to browse for video"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self._load_video(file_path)
    
    def _load_video(self, file_path):
        """Load video and get its duration and bitrate using ffprobe."""
        try:
            self.video_path = file_path
            
            ffprobe_cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            # Use creationflags on Windows to hide console
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True, startupinfo=startupinfo)
            properties = json.loads(result.stdout)
            
            self.video_duration = float(properties['format']['duration'])
            self.is_video_long = self.video_duration >= 3600
            
            # We look for the total format bitrate. If missing, default to 2M.
            try:
                self.video_bitrate = int(properties['format'].get('bit_rate', 0))
                if self.video_bitrate == 0:
                    # Fallback: try to sum up stream bitrates
                    v_br = 0
                    a_br = 0
                    for stream in properties['streams']:
                        if stream['codec_type'] == 'video':
                            v_br = int(stream.get('bit_rate', 2000000))
                        elif stream['codec_type'] == 'audio':
                            a_br = int(stream.get('bit_rate', 128000))
                    self.video_bitrate = v_br + a_br
            except Exception:
                self.video_bitrate = 2000000 # 2Mbps default fallback

            for row in self.segment_rows:
                row.start_time.toggle_hour_field(self.is_video_long)
                row.end_time.toggle_hour_field(self.is_video_long)
            
            # Update UI
            filename = os.path.basename(file_path)
            duration_str = self._format_time(self.video_duration)
            
            # Show bitrate in UI for confirmation
            bitrate_mbps = self.video_bitrate / 1000000
            
            self.file_label.config(
                text=f"{filename} ({duration_str}, ~{bitrate_mbps:.2f} Mbps)",
                foreground='black'
            )
            self.status_label.config(text="Video loaded successfully!", foreground='green')
            self.progress_var.set(0)
            self.progress_label.config(text="0%")

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to probe video with ffprobe: {e.stderr}")
            self.status_label.config(text="Error loading video", foreground='red')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video: {str(e)}")
            self.status_label.config(text="Error loading video", foreground='red')
    
    def _format_time(self, seconds):
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _add_segment(self):
        """Add a new segment row"""
        segment_num = len(self.segment_rows) + 1
        row = SegmentRow(self.segments_container, segment_num, self._delete_segment)
        row.pack(fill=tk.X, pady=5)
        self.segment_rows.append(row)

        # Set toggle state based on video length
        row.start_time.toggle_hour_field(self.is_video_long)
        row.end_time.toggle_hour_field(self.is_video_long)
        
        # If not the first segment, link the previous end time to this new start time for Tab key
        if len(self.segment_rows) > 1:
             prev_row = self.segment_rows[-2]
             prev_row.end_time.set_next_field(row.start_time.entries[0])
    
    def _delete_segment(self, row):
        """Delete a segment row"""
        if len(self.segment_rows) <= 1:
            messagebox.showwarning("Warning", "You must have at least one segment.")
            return
        
        # Find index to repair Tab navigation links later if needed
        idx = self.segment_rows.index(row)
        
        self.segment_rows.remove(row)
        row.destroy()
        
        # Renumber remaining segments and fix Tab navigation links
        for i, segment_row in enumerate(self.segment_rows):
            segment_row.update_label(i + 1)
            # Re-link Tab navigation
            if i < len(self.segment_rows) - 1:
                segment_row.end_time.set_next_field(self.segment_rows[i+1].start_time.entries[0])
            else:
                segment_row.end_time.next_external_field = None

    def _validate_segments(self):
        """Validate all segments"""
        if not self.video_path:
            messagebox.showerror("Error", "Please select a video file first.")
            return False
        
        segments = []
        
        for i, row in enumerate(self.segment_rows):
            segment = row.get_segment()
            
            if segment is None:
                messagebox.showerror("Error", f"Segment {i + 1} has invalid time values.")
                return False
            
            start, end = segment
            
            if start >= end:
                messagebox.showerror("Error", f"Segment {i + 1}: Start time must be before end time.")
                return False
            
            if end > self.video_duration:
                messagebox.showerror("Error", 
                    f"Segment {i + 1}: End time exceeds video duration ({self._format_time(self.video_duration)}).")
                return False
            
            segments.append((start, end))
        
        # Check for overlapping segments
        segments.sort()
        for i in range(len(segments) - 1):
            if segments[i][1] > segments[i + 1][0]:
                messagebox.showerror("Error", 
                    f"Segments overlap: Segment ending at {self._format_time(segments[i][1])} overlaps with segment starting at {self._format_time(segments[i + 1][0])}.")
                return False
        
        return segments
    
    def _process_video(self):
        """Validates segments and starts the processing in a separate thread."""
        if self.is_processing:
            return

        final_segments = self._validate_segments()
        if not final_segments:
            return

        self.is_processing = True
        
        # Disable the process button to prevent multiple clicks
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Button) and "Process" in widget.cget('text'):
                widget.config(state=tk.DISABLED)
                self.process_button = widget # Save reference to re-enable later
                break

        self.progress_var.set(0)
        self.status_label.config(text="Starting video processing...", foreground='blue')
        self.update_idletasks()

        # Run the heavy processing in a separate thread
        processing_thread = threading.Thread(
            target=self._run_ffmpeg_processing,
            args=(final_segments,),
            daemon=True
        )
        processing_thread.start()

    def _update_progress(self, percentage, message=None):
        """Update the progress bar and label safely from thread"""
        self.progress_var.set(percentage)
        self.progress_label.config(text=f"{int(percentage)}%")
        if message:
            self.status_label.config(text=message)

    def _run_ffmpeg_processing(self, segments):
        """
        Runs the FFmpeg command and parses stderr for progress.
        Matches original bitrate.
        """
        temp_icon = None
        include_overlay = self.show_overlay_var.get()

        try:
            # Generate output filename
            directory = os.path.dirname(self.video_path)
            filename = os.path.basename(self.video_path)
            name_part, ext_part = os.path.splitext(filename)
            
            suffix = "_redacted" if include_overlay else "_redacted_fast"
            output_path = os.path.join(directory, f"{name_part}{suffix}{ext_part}")
            ffmpeg_path = self.ffmpeg_path

            ffmpeg_cmd = [ffmpeg_path, '-y', '-i', self.video_path]

            # --- LOGIC BRANCHING ---
            if include_overlay:
                # === Standard Mode: Overlay + Re-encode ===
                
                # Check if mute icon exists
                mute_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mute_2.png')
                if not os.path.exists(mute_icon_path):
                    raise FileNotFoundError("mute_2.png not found in program directory.")

                # Get video height to calculate icon size
                clip = VideoFileClip(self.video_path)
                icon_size = int(clip.h / 5)
                clip.close()

                # Prepare resized mute icon
                temp_dir = tempfile.gettempdir()
                temp_icon = os.path.join(temp_dir, 'hashbrown-temp_resized_icon.png')
                icon_img = Image.open(mute_icon_path)
                icon_img.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
                icon_img.save(temp_icon)

                # Add icon input
                ffmpeg_cmd.extend(['-i', temp_icon])
                
                video_overlay_enables = "+".join([f"between(t,{start},{end})" for start, end in segments])
                video_filter = f"[0:v][1:v]overlay=5:5:enable='{video_overlay_enables}'[v_out]"

                audio_mute_enables = "+".join([f"between(t,{start},{end})" for start, end in segments])
                audio_filter = f"[0:a]volume=enable='{audio_mute_enables}':volume=0[a_out]"
                
                filter_complex = f"{video_filter};{audio_filter}"
                
                ffmpeg_cmd.extend([
                    '-filter_complex', filter_complex,
                    '-map', '[v_out]', 
                    '-map', '[a_out]', 
                ])

                # Check for NVENC
                try:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    encoders = subprocess.check_output([ffmpeg_path, '-encoders'], 
                                                    text=True, 
                                                    startupinfo=startupinfo, 
                                                    stderr=subprocess.STDOUT)
                    has_nvenc = 'h264_nvenc' in encoders
                except Exception:
                    has_nvenc = False
                
                # Calculate bitrates
                target_audio_bitrate = 128000
                target_video_bitrate = max(100000, self.video_bitrate - target_audio_bitrate) 
                v_bitrate_str = f"{target_video_bitrate}"
                a_bitrate_str = f"{target_audio_bitrate}"

                msg_prefix = "Processing..."
                if has_nvenc:
                    self.after(0, lambda: self.status_label.config(text=f"{msg_prefix} (Using NVIDIA NVENC)", foreground='blue'))
                    ffmpeg_cmd.extend(['-c:v', 'h264_nvenc', '-preset', 'p4', '-b:v', v_bitrate_str])
                else:
                    self.after(0, lambda: self.status_label.config(text=f"{msg_prefix} (Using CPU x264)", foreground='blue'))
                    ffmpeg_cmd.extend(['-c:v', 'libx264', '-preset', 'fast', '-b:v', v_bitrate_str])

                ffmpeg_cmd.extend(['-c:a', 'aac', '-b:a', a_bitrate_str])

            else:
                # === Fast Mode: No Overlay + Stream Copy ===
                self.after(0, lambda: self.status_label.config(text="Processing... (Fast Mode - Stream Copy)", foreground='blue'))
                
                # Build audio filter string (without [0:a] labels for -af)
                audio_mute_enables = "+".join([f"between(t,{start},{end})" for start, end in segments])
                audio_filter = f"volume=enable='{audio_mute_enables}':volume=0"
                
                # Use -af (simple audio filter) instead of -filter_complex.
                # This ensures FFmpeg doesn't get confused and try to process the video.
                ffmpeg_cmd.extend([
                    '-c:v', 'copy',      # Direct stream copy (no re-encoding)
                    '-af', audio_filter, # Simple audio filter chain
                    '-c:a', 'aac',       # Re-encode audio to apply filter
                    '-b:a', '128k'       # Default decent audio bitrate
                ])

            # Output file path is last argument
            ffmpeg_cmd.append(output_path)

            # --- Run Process with Progress Parsing ---
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                creationflags=creation_flags
            )

            # Regex to find time=HH:MM:SS.mm
            time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d+)")

            while True:
                line = process.stderr.readline()
                if line == '' and process.poll() is not None:
                    break
                
                if line:
                    match = time_pattern.search(line)
                    if match:
                        h, m, s = match.groups()
                        current_seconds = int(h) * 3600 + int(m) * 60 + float(s)
                        
                        if self.video_duration and self.video_duration > 0:
                            percentage = (current_seconds / self.video_duration) * 100
                            percentage = min(percentage, 99.9) # Cap at 99 until finished
                            self.after(0, lambda p=percentage: self._update_progress(p))

            return_code = process.wait()
            
            if return_code == 0:
                self.after(0, lambda: self._update_progress(100, "Finished!"))
                success_msg = f"Video processed successfully! Saved to:\n{output_path}"
                self.after(0, lambda: messagebox.showinfo("Success", success_msg))
                self.after(0, lambda: self.status_label.config(text="Processing complete.", foreground='green'))
            else:
                raise subprocess.CalledProcessError(return_code, ffmpeg_cmd)

        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg Error (Code {e.returncode})"
            self.after(0, lambda: self.status_label.config(text=error_msg, foreground='red'))
            self.after(0, lambda: messagebox.showerror("Error", error_msg))
            print(e)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            self.after(0, lambda: self.status_label.config(text="Error during processing", foreground='red'))
            self.after(0, lambda: messagebox.showerror("Error", error_msg))
            print(e)
        finally:
            self.is_processing = False
            if temp_icon and os.path.exists(temp_icon):
                try:
                    os.remove(temp_icon)
                except:
                    pass
            if hasattr(self, 'process_button'):
                self.after(0, lambda: self.process_button.config(state=tk.NORMAL))

def main():
    app = HashbrownApp()
    app.mainloop()


if __name__ == "__main__":
    main()