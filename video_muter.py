import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import re
try:
    # Try newer moviepy import structure (v2.x)
    from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, AudioClip
except ImportError:
    # Fall back to older import structure (v1.x)
    from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
    from moviepy.audio.AudioClip import AudioClip
import numpy as np
import subprocess
from PIL import Image


class TimeInputField(ttk.Frame):
    """Custom time input field with HH:MM:SS format and auto-navigation"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.entries = []
        self.next_external_field = None  # For cross-TimeInputField navigation
        
        # Hour field
        self.hour_var = tk.StringVar()
        self.hour_entry = ttk.Entry(self, textvariable=self.hour_var, width=3, justify='center')
        self.hour_entry.pack(side=tk.LEFT)
        self.entries.append(self.hour_entry)
        
        ttk.Label(self, text=":").pack(side=tk.LEFT)
        
        # Minute field
        self.min_var = tk.StringVar()
        self.min_entry = ttk.Entry(self, textvariable=self.min_var, width=3, justify='center')
        self.min_entry.pack(side=tk.LEFT)
        self.entries.append(self.min_entry)
        
        ttk.Label(self, text=":").pack(side=tk.LEFT)
        
        # Second field
        self.sec_var = tk.StringVar()
        self.sec_entry = ttk.Entry(self, textvariable=self.sec_var, width=3, justify='center')
        self.sec_entry.pack(side=tk.LEFT)
        self.entries.append(self.sec_entry)
        
        # Bind events for auto-navigation
        self._setup_bindings()
    
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
        # Only allow numbers and navigation keys
        if event.char and not event.char.isdigit():
            return 'break'
        
        entry = self.entries[index]
        current_value = entry.get()
        
        # Limit to 2 digits
        if len(current_value) >= 2:
            # If we already have 2 digits, move to next field and prevent this digit
            if index < len(self.entries) - 1:
                self.entries[index + 1].focus()
                self.entries[index + 1].icursor(0)
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
        cursor_pos = entry.index(tk.INSERT)
        
        # If at the beginning of the field and not the first field, go back
        if cursor_pos == 0 and index > 0:
            self.entries[index - 1].focus()
            self.entries[index - 1].icursor(tk.END)
            return 'break'
        
        return None
    
    def get_value(self):
        """Get the time value in seconds"""
        try:
            hours = int(self.hour_var.get() or 0)
            minutes = int(self.min_var.get() or 0)
            seconds = int(self.sec_var.get() or 0)
            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return None
    
    def get_formatted_value(self):
        """Get the time value formatted as HH:MM:SS"""
        hours = self.hour_var.get().zfill(2)
        minutes = self.min_var.get().zfill(2)
        seconds = self.sec_var.get().zfill(2)
        return f"{hours}:{minutes}:{seconds}"
    
    def set_value(self, hours=0, minutes=0, seconds=0):
        """Set the time value"""
        self.hour_var.set(str(hours).zfill(2))
        self.min_var.set(str(minutes).zfill(2))
        self.sec_var.set(str(seconds).zfill(2))


class SegmentRow(ttk.Frame):
    """A single segment row with start/end times and delete button"""
    
    def __init__(self, parent, segment_num, on_delete, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.segment_num = segment_num
        self.on_delete = on_delete
        
        # Segment label
        ttk.Label(self, text=f"Segment {segment_num}:").pack(side=tk.LEFT, padx=5)
        
        # Start time
        ttk.Label(self, text="Start:").pack(side=tk.LEFT, padx=5)
        self.start_time = TimeInputField(self)
        self.start_time.pack(side=tk.LEFT, padx=5)
        
        # End time
        ttk.Label(self, text="End:").pack(side=tk.LEFT, padx=5)
        self.end_time = TimeInputField(self)
        self.end_time.pack(side=tk.LEFT, padx=5)
        
        # Link the start and end time fields for navigation
        self.start_time.set_next_field(self.end_time.entries[0])
        
        # Delete button
        self.delete_btn = ttk.Button(self, text="✕", width=3, command=self._on_delete_click)
        self.delete_btn.pack(side=tk.LEFT, padx=5)
    
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
            if isinstance(widget, ttk.Label) and widget.cget('text').startswith('Segment'):
                widget.config(text=f"Segment {num}:")
                break


class VideoMuterApp(TkinterDnD.Tk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Hashbrown")
        self.geometry("700x600")
        
        # Set window icon
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png')
        if os.path.exists(logo_path):
            try:
                self.iconphoto(True, tk.PhotoImage(file=logo_path))
            except Exception:
                pass  # If logo fails to load as icon, continue without it
        
        self.video_path = None
        self.video_duration = None
        self.segment_rows = []
        
        self._create_widgets()
        self._setup_drag_drop()
    
    def _create_widgets(self):
        """Create all GUI widgets"""
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
        segments_frame = ttk.LabelFrame(self, text="Mute Segments", padding=10)
        segments_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Scrollable frame for segments
        canvas = tk.Canvas(segments_frame, height=300)
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
        ttk.Button(segments_frame, text="+ Add Segment", command=self._add_segment).pack(pady=10)
        
        # Add first segment by default
        self._add_segment()
        
        # Process button
        process_btn = ttk.Button(self, text="Process Video", command=self._process_video, 
                                 style='Accent.TButton')
        process_btn.pack(pady=20)
        
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
        """Load video and get its duration"""
        try:
            self.video_path = file_path
            
            # Get video duration
            clip = VideoFileClip(file_path)
            self.video_duration = clip.duration
            clip.close()
            
            # Update UI
            filename = os.path.basename(file_path)
            duration_str = self._format_time(self.video_duration)
            self.file_label.config(
                text=f"{filename} (Duration: {duration_str})",
                foreground='black'
            )
            self.status_label.config(text="Video loaded successfully!", foreground='green')
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
    
    def _delete_segment(self, row):
        """Delete a segment row"""
        if len(self.segment_rows) <= 1:
            messagebox.showwarning("Warning", "You must have at least one segment.")
            return
        
        self.segment_rows.remove(row)
        row.destroy()
        
        # Renumber remaining segments
        for i, segment_row in enumerate(self.segment_rows):
            segment_row.update_label(i + 1)
    
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
        """Process the video with mute segments"""
        segments = self._validate_segments()
        
        if not segments:
            return
        
        try:
            self.status_label.config(text="Processing video... Please wait.", foreground='blue')
            self.update()
            
            # Generate output filename
            directory = os.path.dirname(self.video_path)
            filename = os.path.basename(self.video_path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(directory, f"processed-{filename}")
            
            # Load video
            video = VideoFileClip(self.video_path)
            
            # Check if mute.png exists
            mute_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mute.png')
            if not os.path.exists(mute_icon_path):
                messagebox.showerror("Error", "mute.png not found in program directory.")
                self.status_label.config(text="Error: mute.png not found", foreground='red')
                return
            
            # Calculate mute icon size (1/5 of video height)
            icon_size = int(video.h / 5)
            
            # Create segments list for ffmpeg filter
            # We'll use ffmpeg's overlay filter which is much faster
            filter_complex_parts = []
            
            for i, (start, end) in enumerate(segments):
                # Format times for ffmpeg
                filter_complex_parts.append(
                    f"[0:v][1:v]overlay=0:0:enable='between(t,{start},{end})'[v{i}]"
                )
            
            # Build the final filter
            if len(filter_complex_parts) == 1:
                filter_complex = filter_complex_parts[0].replace('[v0]', '[outv]')
            else:
                # Chain multiple overlays
                filter_complex = filter_complex_parts[0]
                for i in range(1, len(filter_complex_parts)):
                    prev = f'[v{i-1}]'
                    curr = filter_complex_parts[i].replace('[0:v]', prev)
                    if i == len(filter_complex_parts) - 1:
                        curr = curr.replace(f'[v{i}]', '[outv]')
                    filter_complex += ';' + curr
            
            # Mute audio segments
            audio = video.audio
            if audio is not None:
                # Get original audio
                original_audio = video.audio
                
                # Create new audio with muted segments
                def make_frame(t):
                    # Handle both single time values and arrays of time values
                    frame = original_audio.get_frame(t)
                    
                    # Check if t is an array or single value
                    if isinstance(t, (int, float)):
                        # Single time value
                        for start, end in segments:
                            if start <= t < end:
                                return frame * 0  # Mute
                        return frame
                    else:
                        # Array of time values
                        result = frame.copy()
                        t_array = np.asarray(t)
                        for start, end in segments:
                            mask = (t_array >= start) & (t_array < end)
                            if result.ndim == 1:
                                result[mask] = 0
                            else:
                                result[mask] = 0
                        return result
                
                muted_audio = AudioClip(make_frame, duration=video.duration, fps=original_audio.fps)
                
                # Save audio temporarily
                muted_audio.write_audiofile('temp-muted-audio.m4a', codec='aac')
            
            # Close video to release resources
            video.close()
            
            # Get ffmpeg path from imageio_ffmpeg
            try:
                import imageio_ffmpeg
                ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            except:
                ffmpeg_path = 'ffmpeg'  # Fall back to system ffmpeg
            
            # Now use direct ffmpeg for much faster processing with GPU acceleration
            import subprocess
            
            # Prepare mute icon overlay with size
            temp_icon = 'temp_resized_icon.png'
            from PIL import Image
            icon_img = Image.open(mute_icon_path)
            icon_img.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
            icon_img.save(temp_icon)
            
            # Build ffmpeg command - remove CUDA since bundled ffmpeg doesn't support it
            # We'll still use NVENC for encoding which is much faster
            ffmpeg_cmd = [
                ffmpeg_path,
                '-y',  # Overwrite output
                '-i', self.video_path,
                '-i', temp_icon,
            ]
            
            # Add audio input if we have muted audio
            if audio is not None:
                ffmpeg_cmd.extend(['-i', 'temp-muted-audio.m4a'])
            
            # Build filter complex for conditional overlay
            overlay_filters = []
            for start, end in segments:
                overlay_filters.append(f"between(t,{start},{end})")
            
            overlay_enable = '+'.join(overlay_filters) if overlay_filters else '0'
            
            filter_complex = f"[0:v][1:v]overlay=0:0:enable='{overlay_enable}'[outv]"
            
            ffmpeg_cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[outv]',
            ])
            
            # Map audio
            if audio is not None:
                ffmpeg_cmd.extend(['-map', '2:a'])  # Use muted audio from third input
            else:
                ffmpeg_cmd.extend(['-map', '0:a?'])  # Copy original audio if exists
            
            # Check if NVENC is available, otherwise use CPU encoding
            try:
                # Test if NVENC is available
                test_cmd = [ffmpeg_path, '-hide_banner', '-encoders']
                result = subprocess.run(test_cmd, capture_output=True, text=True)
                has_nvenc = 'h264_nvenc' in result.stdout
            except:
                has_nvenc = False
            
            # Encoding settings
            if has_nvenc:
                # Use NVIDIA hardware encoding
                ffmpeg_cmd.extend([
                    '-c:v', 'h264_nvenc',
                    '-preset', 'p4',
                    '-rc:v', 'vbr',
                    '-cq:v', '23',
                    '-b:v', '10M',
                    '-maxrate:v', '15M',
                ])
            else:
                # Fall back to CPU encoding with fast settings
                ffmpeg_cmd.extend([
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',
                ])
            
            ffmpeg_cmd.extend([
                '-c:a', 'aac',
                '-b:a', '192k',
                output_path
            ])
            
            # Run ffmpeg
            try:
                process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as e:
                # Clean up temporary files
                if os.path.exists('temp-muted-audio.m4a'):
                    os.remove('temp-muted-audio.m4a')
                if os.path.exists(temp_icon):
                    os.remove(temp_icon)
                raise Exception(f"FFmpeg error: {e.stderr}")
            except FileNotFoundError:
                # Clean up temporary files
                if os.path.exists('temp-muted-audio.m4a'):
                    os.remove('temp-muted-audio.m4a')
                if os.path.exists(temp_icon):
                    os.remove(temp_icon)
                raise Exception("FFmpeg not found. Please ensure FFmpeg is installed and in your PATH.")
            
            # Clean up temporary files
            if os.path.exists('temp-muted-audio.m4a'):
                os.remove('temp-muted-audio.m4a')
            if os.path.exists(temp_icon):
                os.remove(temp_icon)
            
            self.status_label.config(
                text=f"Video processed successfully! Saved as: {os.path.basename(output_path)}",
                foreground='green'
            )
            messagebox.showinfo("Success", f"Video saved as:\n{output_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process video:\n{str(e)}")
            self.status_label.config(text="Error processing video", foreground='red')


def main():
    app = VideoMuterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
