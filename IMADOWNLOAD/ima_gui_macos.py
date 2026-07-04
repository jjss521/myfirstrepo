"""
IMA Knowledge Base Downloader - macOS Style GUI
Apple-inspired light theme with San Francisco-like aesthetics
"""

import customtkinter as ctk
import threading
import json
import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

API_BASE = "https://ima.qq.com/cgi-bin/knowledge_share_get/get_share_info"
PAGE_SIZE = 50
MEDIA_TYPE_NOTE = 11
MEDIA_TYPE_FOLDER = 99


class macOSApp(ctk.CTk):
    """macOS-style light themed application"""
    
    def __init__(self):
        super().__init__()

        self.title("IMA Knowledge Base Downloader")
        self.geometry("1100x780")
        self.minsize(950, 680)
        
        # macOS light theme colors
        self.configure(fg_color="#F5F5F7")
        
        self.downloading = False
        self.cancel_flag = False
        self.scanned_data = None
        self.best_sid = None
        self.kb_dir = ""
        self.tree_items = {}
        
        # Apply macOS font style
        self._setup_fonts()
        
        self._create_widgets()

    def _setup_fonts(self):
        """Setup SF Pro-like font stack"""
        # macOS system font stack
        mac_font = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
        # Monospace for logs
        mono_font = '-apple-system, "Menlo", "Monaco", "Courier New", monospace'
        
        # Store font references
        self.fonts = {
            'header': (mac_font, 24, 'bold'),
            'title': (mac_font, 17, 'bold'),
            'subtitle': (mac_font, 13, 'normal'),
            'body': (mac_font, 13, 'normal'),
            'small': (mac_font, 11, 'normal'),
            'label': (mac_font, 12, 'normal'),
            'button': (mac_font, 13, 'semibold'),
            'stat': (mac_font, 22, 'bold'),
            'stat_label': (mac_font, 11, 'normal'),
            'log': (mono_font, 11, 'normal'),
        }
    
    def _create_widgets(self):
        # Main container
        main = ctk.CTkFrame(self, fg_color="#F5F5F7")
        main.pack(fill="both", expand=True, padx=20, pady=16)
        
        # Title
        ctk.CTkLabel(main, text="IMA Knowledge Base Downloader",
                      font=ctk.CTkFont(size=24, weight="bold", family="-apple-system"),
                      text_color="#1D1D1F").pack(pady=(0, 12))
        
        # URL Input Section
        input_frame = self._create_card(main, "#FFFFFF")
        input_frame.pack(fill="x", pady=(0, 12))
        
        row1 = ctk.CTkFrame(input_frame, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(12, 6))
        
        ctk.CTkLabel(row1, text="Share URL", font=ctk.CTkFont(size=12, weight="semibold", family="-apple-system"),
                      text_color="#6E6E73").pack(anchor="w")
        
        self.url_entry = ctk.CTkEntry(row1, 
                                       placeholder_text="https://ima.qq.com/wiki/?shareId=...", 
                                       height=32,
                                       font=ctk.CTkFont(size=13, family="-apple-system"), 
                                       fg_color="#F5F5F7", 
                                       border_color="transparent", 
                                       border_width=0,
                                       corner_radius=6)
        self.url_entry.pack(fill="x", pady=(4, 0))
        
        row2 = ctk.CTkFrame(input_frame, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(8, 12))
        
        ctk.CTkLabel(row2, text="Output Directory", font=ctk.CTkFont(size=12, weight="semibold", family="-apple-system"),
                      text_color="#6E6E73").pack(anchor="w")
        
        dir_row = ctk.CTkFrame(row2, fg_color="transparent")
        dir_row.pack(fill="x", pady=(4, 0))
        
        self.dir_entry = ctk.CTkEntry(dir_row, height=32, font=ctk.CTkFont(size=13, family="-apple-system"),
                                       fg_color="#F5F5F7", border_color="transparent", border_width=0, corner_radius=6)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.dir_entry.insert(0, "E:\\IMA_DOWNLOADS")
        
        browse_btn = ctk.CTkButton(dir_row, text="Browse", width=72, height=32, 
                                    font=ctk.CTkFont(size=12, weight="semibold", family="-apple-system"),
                                    fg_color="#F5F5F7", hover_color="#E8E8ED",
                                    border_color="transparent", corner_radius=6,
                                    command=self._browse_dir)
        browse_btn.pack(side="right")
        
        # Action Buttons
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 12))
        
        button_configs = [
            ("Scan", "#007AFF", "#0051D5", self._start_scan),
            ("Download Selected", "#34C759", "#248A3D", self._start_download, "disabled"),
            ("Download All", "#5856D6", "#3634A3", self._start_download_all, "disabled"),
            ("Stop", "#FF3B30", "#CC2F26", self._stop_download, "disabled"),
        ]
        
        for text, fg_color, hover_color, cmd, *rest in button_configs:
            state = rest[0] if rest else "normal"
            btn = ctk.CTkButton(btn_frame, text=text, height=32, width=128,
                               font=ctk.CTkFont(size=13, weight="semibold", family="-apple-system"),
                               fg_color=fg_color, hover_color=hover_color, corner_radius=6,
                               border_color="transparent",
                               command=cmd, state=state)
            btn.pack(side="left", expand=True, fill="x", padx=4)
        
        # Stats Card
        stats_frame = self._create_card(main, "#FFFFFF")
        stats_frame.pack(fill="x", pady=(0, 12))
        
        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=16, pady=10)
        
        stat_configs = [
            ("Total", "0", "#007AFF"),
            ("Downloaded", "0", "#34C759"),
            ("Failed", "0", "#FF3B30"),
            ("Skipped", "0", "#8E8E93"),
        ]
        
        for label, value, color in stat_configs:
            stat_widget = self._create_stat_box(stats_inner, label, value, color)
            stat_widget[1].pack(side="left", expand=True, fill="both", padx=(0, 24))
        
        # Progress Card
        progress_frame = self._create_card(main, "#FFFFFF")
        progress_frame.pack(fill="x", pady=(0, 12))
        
        progress_inner = ctk.CTkFrame(progress_frame, fg_color="transparent")
        progress_inner.pack(fill="x", padx=16, pady=8)
        
        self.progress_label = ctk.CTkLabel(progress_inner, text="Ready", 
                                            font=ctk.CTkFont(size=11, family="-apple-system"), 
                                            text_color="#8E8E93")
        self.progress_label.pack(anchor="w", pady=(0, 4))
        
        self.progress_bar = ctk.CTkProgressBar(progress_inner, height=4, corner_radius=2, 
                                                progress_color="#007AFF")
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        
        # Bottom Section
        bottom = ctk.CTkFrame(main, fg_color="transparent")
        bottom.pack(fill="both", expand=True)
        
        # Tree View (Directory Structure)
        tree_frame = self._create_card(bottom, "#FFFFFF")
        tree_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        tree_header = ctk.CTkFrame(tree_frame, fg_color="transparent")
        tree_header.pack(fill="x", padx=16, pady=(12, 4))
        
        ctk.CTkLabel(tree_header, text="Directory Structure", 
                     font=ctk.CTkFont(size=13, weight="semibold", family="-apple-system"),
                     text_color="#1D1D1F").pack(side="left")
        
        self.select_count_label = ctk.CTkLabel(tree_header, text="", 
                                               font=ctk.CTkFont(size=11, family="-apple-system"),
                                               text_color="#007AFF")
        self.select_count_label.pack(side="right")
        
        # Tree Control Buttons
        tree_btn_row = ctk.CTkFrame(tree_frame, fg_color="transparent")
        tree_btn_row.pack(fill="x", padx=16, pady=(0, 4))
        
        tree_btn_configs = [
            ("Check All", "#007AFF", "#0051D5"),
            ("Uncheck All", "#8E8E93", "#636366"),
            ("Expand All", "#8E8E93", "#636366"),
        ]
        
        for text, fg_color, hover_color in tree_btn_configs:
            btn = ctk.CTkButton(tree_btn_row, text=text, width=72, height=24, 
                               font=ctk.CTkFont(size=11, family="-apple-system"),
                               fg_color=fg_color, hover_color=hover_color, corner_radius=4,
                               border_color="transparent",
                               command={"Check All": self._check_all, 
                                       "Uncheck All": self._uncheck_all,
                                       "Expand All": self._expand_all}[text])
            btn.pack(side="left", padx=(0, 6))
        
        # Tree Container
        tree_container = ctk.CTkFrame(tree_frame, fg_color="#FFFFFF", corner_radius=0)
        tree_container.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        
        # Custom Treeview style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("macOS.Treeview",
                       background="#FFFFFF", 
                       foreground="#1D1D1F",
                       fieldbackground="#FFFFFF", 
                       borderwidth=0,
                       font=("-apple-system", 12),
                       rowheight=28)
        style.configure("macOS.Treeview.Heading",
                       background="#F5F5F7", 
                       foreground="#6E6E73",
                       font=("-apple-system", 11, "bold"))
        style.map("macOS.Treeview", 
                 background=[("selected", "#E8F0FE")], 
                 foreground=[("selected", "#0051D5")])
        
        tree_scroll = ttk.Scrollbar(tree_container, orient="vertical", style="macOS.TScrollbar")
        tree_scroll.pack(side="right", fill="y")
        
        self.tree = ttk.Treeview(tree_container, style="macOS.Treeview", 
                                yscrollcommand=tree_scroll.set,
                                columns=("size", "type"), selectmode="none")
        tree_scroll.config(command=self.tree.yview)
        
        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.heading("size", text="Size", anchor="e")
        self.tree.heading("type", text="Type", anchor="w")
        self.tree.column("#0", width=380, minwidth=220)
        self.tree.column("size", width=80, minwidth=60, anchor="e")
        self.tree.column("type", width=60, minwidth=50)
        self.tree.pack(fill="both", expand=True)
        
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", self._on_tree_toggle)
        
        # Log Panel
        log_frame = self._create_card(bottom, "#FFFFFF")
        log_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))
        
        ctk.CTkLabel(log_frame, text="Activity Log", 
                     font=ctk.CTkFont(size=13, weight="semibold", family="-apple-system"),
                     text_color="#1D1D1F").pack(anchor="w", padx=16, pady=(12, 4))
        
        self.log_text = ctk.CTkTextbox(log_frame, 
                                       font=ctk.CTkFont(family="Menlo", size=11),
                                       fg_color="#F5F5F7", 
                                       text_color="#1D1D1F", 
                                       corner_radius=6,
                                       border_width=0)
        self.log_text.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        
        self._log("Ready. Paste a share URL and click Scan.")

    def _create_card(self, parent, bg_color="#FFFFFF"):
        """Create a macOS style card"""
        return ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=12)

    def _create_stat_box(self, parent, label, value, color):
        """Create a stat display box"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11, family="-apple-system"),
                      text_color="#8E8E93").pack()
        lbl = ctk.CTkLabel(frame, text=value, 
                          font=ctk.CTkFont(size=22, weight="bold", family="-apple-system"),
                          text_color=color)
        lbl.pack()
        return (lbl, frame)

    def _log(self, msg):
        """Log message with timestamp"""
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")

    def _browse_dir(self):
        """Browse directory"""
        d = filedialog.askdirectory(title="Select Output Directory")
        if d:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, d)

    def _set_state(self, scanning=False, downloading=False):
        """Update button states"""
        try:
            buttons = [
                (self.scan_btn, {"scanning": ("disabled", "#8E8E93"), 
                               "downloading": ("disabled", "#8E8E93"),
                               "normal": ("normal", "#007AFF")}),
                (self.download_btn, {"scanning": ("disabled", "#8E8E93"), 
                                   "downloading": ("disabled", "#8E8E93"),
                                   "normal": ("normal", "#34C759")}),
                (self.download_all_btn, {"scanning": ("disabled", "#8E8E93"), 
                                       "downloading": ("disabled", "#8E8E93"),
                                       "normal": ("normal", "#5856D6")}),
                (self.stop_btn, {"scanning": ("normal", "#FF3B30"), 
                               "downloading": ("normal", "#FF3B30"),
                               "normal": ("disabled", "#8E8E93")}),
            ]
            
            for btn, states in buttons:
                state_config = states.get("scanning" if scanning else "downloading" if downloading else "normal")
                btn.configure(state=state_config[0], fg_color=state_config[1])
            
            # Enable/disable inputs
            self.url_entry.configure(state="disabled" if (scanning or downloading) else "normal")
            self.dir_entry.configure(state="disabled" if (scanning or downloading) else "normal")
            
        except Exception as e:
            print(f"_set_state error: {e}")

    def _stop_download(self):
        """Stop download"""
        self.cancel_flag = True
        self._log("Stopping download...")

    def _update_stat(self, label, value):
        """Update stat label"""
        label[0].configure(text=str(value))

    def _update_progress(self, current, total, text=""):
        """Update progress bar"""
        if total > 0:
            self.progress_bar.set(current / total)
        self.progress_label.configure(text=text)

    # --- Rest of the methods remain the same as original ---
    # (Scan, download, tree operations - unchanged logic)
    
    def _start_scan(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a share URL")
            return
        if not requests:
            messagebox.showerror("Error", "requests not installed")
            return
        self._set_state(scanning=True)
        self.cancel_flag = False
        threading.Thread(target=self._scan_worker, args=(url,), daemon=True).start()

    def _scan_worker(self, url):
        try:
            share_id = self._extract_share_id(url)
            self.after(0, self._log, f"Scanning shareId: ...{share_id[-16:]}")

            candidates = self._find_valid_share_id(share_id)
            self.after(0, self._log, f"Trying {len(candidates)} candidates...")

            best_data = None
            best_sid = None

            for i, sid in enumerate(candidates):
                if self.cancel_flag:
                    self.after(0, self._log, "Cancelled")
                    return

                self.after(0, self._log, f"Candidate {i + 1}/{len(candidates)}...")
                try:
                    data = self._api_get_share_info(sid)
                except Exception as api_err:
                    self.after(0, self._log, f"  API error: {str(api_err)[:60]}")
                    data = None

                if data:
                    best_data = data
                    best_sid = sid
                    self.after(0, self._log, "Found valid shareId!")
                    break

            if not best_data:
                self.after(0, self._log, "ERROR: Invalid shareId or auth required")
                return

            kb_info = best_data.get("knowledge_base_info", {}).get("basic_info", {})
            kb_name = self._sanitize(kb_info.get("name", "unknown"))
            output_dir = self.dir_entry.get().strip() or "ima_downloads"
            kb_dir = os.path.join(output_dir, kb_name)
            os.makedirs(kb_dir, exist_ok=True)

            self.scanned_data = best_data
            self.best_sid = best_sid
            self.kb_dir = kb_dir

            self.after(0, self._log, f"KB: {kb_info.get('name', '?')}")
            self.after(0, self._log, f"Items: {best_data.get('total_size', 0)}")
            self.after(0, self._log, "Building directory tree...")

            tree_data = self._build_tree_data(best_sid, best_data)
            self.after(0, self._populate_tree, tree_data, kb_name)
            self.after(0, self._log, "Scan complete! Select items and click Download.")

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.after(0, self._log, f"ERROR: {e}")
            self.after(0, self._log, tb[-200:])

        finally:
            self.after(0, self._set_state)

    def _build_tree_data(self, share_id, root_data):
        tree = {"name": root_data.get("knowledge_base_info", {}).get("basic_info", {}).get("name", "root"),
                "type": "root", "children": [], "items": [], "share_id": share_id}

        root_items = root_data.get("knowledge_list", [])
        for item in root_items:
            fi = item.get("folder_info")
            if fi:
                folder = {"name": fi.get("name", "?"), "type": "folder",
                          "count": fi.get("file_number", "0"), "folder_id": fi["folder_id"],
                          "children": [], "items": [], "scanned": False, "share_id": share_id,
                          "relative_path": fi.get("name", "?")}
                tree["children"].append(folder)
            else:
                node = self._item_to_node(item)
                node["relative_path"] = ""
                tree["items"].append(node)

        return tree

    def _lazy_scan_folder(self, node):
        if node.get("scanned"):
            return
        share_id = node.get("share_id", self.best_sid)
        folder_id = node.get("folder_id")
        if not folder_id:
            return

        parent_path = node.get("relative_path", "")

        page_cursor = ""
        while True:
            if self.cancel_flag:
                break
            payload = {"shareId": share_id, "limit": PAGE_SIZE, "folder_id": folder_id}
            if page_cursor:
                payload["cursor"] = page_cursor
            try:
                r = requests.post(API_BASE, json=payload, timeout=15)
                d = r.json()
            except Exception:
                break

            if d.get("code") != 0:
                break

            for item in d.get("knowledge_list", []):
                fi = item.get("folder_info")
                if fi:
                    sub_name = fi.get("name", "?")
                    sub = {"name": sub_name, "type": "folder",
                           "count": fi.get("file_number", "0"), "folder_id": fi["folder_id"],
                           "children": [], "items": [], "scanned": False, "share_id": share_id,
                           "relative_path": os.path.join(parent_path, sub_name)}
                    node["children"].append(sub)
                else:
                    item_node = self._item_to_node(item)
                    item_node["relative_path"] = parent_path
                    node["items"].append(item_node)

            if d.get("is_end", True) or not d.get("next_cursor"):
                break
            page_cursor = d["next_cursor"]

        node["scanned"] = True

    def _item_to_node(self, item):
        mt = item.get("media_type", 0)
        type_name = "note" if mt == MEDIA_TYPE_NOTE else "folder" if mt == MEDIA_TYPE_FOLDER else "file"
        size = int(item.get("file_size", "0") or "0")
        return {
            "name": item.get("title", "untitled"),
            "type": type_name,
            "size": size,
            "jump_url": item.get("jump_url", ""),
            "media_type": mt,
            "cover_urls": item.get("cover_urls", []),
        }

    def _populate_tree(self, tree_data, kb_name):
        self.tree.delete(*self.tree.get_children())
        self.tree_items.clear()

        root_id = self.tree.insert("", "end", text=f" {kb_name}", values=("", "KB"), open=True)
        self.tree_items[root_id] = {"checked": True, "node": tree_data}

        for child in tree_data.get("children", []):
            count = child.get("count", "?")
            cid = self.tree.insert(root_id, "end",
                                    text=f" \u2611 {child['name']}",
                                    values=(f"{count} items", "DIR"),
                                    open=False)
            self.tree_items[cid] = {"checked": True, "node": child}

        for item in tree_data.get("items", []):
            size_str = self._format_size(item.get("size", 0))
            type_tag = "NOTE" if item.get("media_type") == MEDIA_TYPE_NOTE else "FILE"
            iid = self.tree.insert(root_id, "end",
                                    text=f" \u2611 {item['name']}",
                                    values=(size_str, type_tag))
            self.tree_items[iid] = {"checked": True, "node": item}

        self.tree.bind("<<TreeviewOpen>>", self._on_tree_open)
        self._update_check_count()

    def _format_size(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / 1024 / 1024:.1f} MB"

    def _on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "tree":
            col = self.tree.identify_column(event.x)
            if col == "#0":
                item_id = self.tree.identify_row(event.y)
                if item_id and item_id in self.tree_items:
                    self._toggle_check(item_id)

    def _on_tree_toggle(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            children = self.tree.get_children(item_id)
            if children:
                if self.tree.item(item_id, "open"):
                    self.tree.item(item_id, open=False)
                else:
                    self.tree.item(item_id, open=True)

    def _on_tree_open(self, event):
        selected = self.tree.focus()
        if not selected or selected not in self.tree_items:
            return

        info = self.tree_items[selected]
        node = info.get("node", {})

        if node.get("type") == "folder" and not node.get("scanned", True):
            self._lazy_scan_folder(node)

            children = self.tree.get_children(selected)
            if children:
                self.tree.delete(*children)

            check_mark = "\u2611" if info.get("checked", True) else "\u2610"

            for child in node.get("children", []):
                count = child.get("count", "?")
                cid = self.tree.insert(selected, "end",
                                        text=f" {check_mark} {child['name']}",
                                        values=(f"{count} items", "DIR"),
                                        open=False)
                self.tree_items[cid] = {"checked": info.get("checked", True), "node": child}

            for item in node.get("items", []):
                size_str = self._format_size(item.get("size", 0))
                type_tag = "NOTE" if item.get("media_type") == MEDIA_TYPE_NOTE else "FILE"
                iid = self.tree.insert(selected, "end",
                                        text=f" {check_mark} {item['name']}",
                                        values=(size_str, type_tag))
                self.tree_items[iid] = {"checked": info.get("checked", True), "node": item}

            self._update_check_count()

    def _toggle_check(self, item_id):
        if item_id not in self.tree_items:
            return
        info = self.tree_items[item_id]
        info["checked"] = not info["checked"]

        self._propagate_check(item_id, info["checked"])
        self._update_check_display(item_id)
        self._update_check_count()

    def _propagate_check(self, item_id, checked):
        if item_id in self.tree_items:
            self.tree_items[item_id]["checked"] = checked
        for child_id in self.tree.get_children(item_id):
            self._propagate_check(child_id, checked)
            self._update_check_display(child_id)

    def _update_check_display(self, item_id):
        if item_id not in self.tree_items:
            return
        info = self.tree_items[item_id]
        node = info["node"]
        mark = "\u2611" if info["checked"] else "\u2610"
        name = node.get("name", "?")
        self.tree.item(item_id, text=f" {mark} {name}")

    def _update_check_count(self):
        total = 0
        checked = 0
        for iid, info in self.tree_items.items():
            if info["node"].get("type") in ("file", "note"):
                total += 1
                if info["checked"]:
                    checked += 1
        self.select_count_label.configure(text=f"{checked}/{total} selected")

    def _check_all(self):
        for iid in self.tree_items:
            self.tree_items[iid]["checked"] = True
            self._update_check_display(iid)
        self._update_check_count()

    def _uncheck_all(self):
        for iid in self.tree_items:
            self.tree_items[iid]["checked"] = False
            self._update_check_display(iid)
        self._update_check_count()

    def _expand_all(self):
        def expand(parent):
            for child in self.tree.get_children(parent):
                self.tree.item(child, open=True)
                expand(child)
        expand("")

    def _get_selected_files(self):
        files = []
        self._collect_selected("", files)
        return files

    def _collect_selected(self, parent, files):
        for child_id in self.tree.get_children(parent):
            info = self.tree_items.get(child_id, {})
            if not info.get("checked"):
                continue
            node = info.get("node", {})
            if node.get("type") in ("file", "note"):
                files.append(node)
            elif node.get("type") in ("folder", "root"):
                if node.get("type") == "folder" and not node.get("scanned", False):
                    self._lazy_scan_folder(node)
                self._collect_node_files(node, files)

    def _collect_node_files(self, node, files):
        for child_node in node.get("children", []):
            if child_node.get("type") == "folder":
                if not child_node.get("scanned", False):
                    self._lazy_scan_folder(child_node)
                self._collect_node_files(child_node, files)
            else:
                files.append(child_node)
        for item_node in node.get("items", []):
            files.append(item_node)

    def _start_download(self):
        files = self._get_selected_files()
        if not files:
            messagebox.showinfo("Info", "No files selected")
            return
        self._begin_download(files)

    def _start_download_all(self):
        for iid in self.tree_items:
            self.tree_items[iid]["checked"] = True
        self._update_check_count()
        files = self._get_selected_files()
        if not files:
            messagebox.showinfo("Info", "No files found")
            return
        self._begin_download(files)

    def _begin_download(self, files):
        self._set_state(downloading=True)
        self.cancel_flag = False
        threading.Thread(target=self._download_worker, args=(files,), daemon=True).start()

    def _download_worker(self, files):
        try:
            total = len(files)
            downloaded = 0
            failed = 0
            skipped = 0

            self.after(0, self._update_stat, self.stat_total, total)

            for i, item in enumerate(files):
                if self.cancel_flag:
                    self.after(0, self._log, "Cancelled")
                    break

                title = item.get("name", "untitled")
                jump_url = item.get("jump_url", "")
                media_type = item.get("media_type", 0)

                ext = self._get_file_ext(title, jump_url)
                safe_title = self._sanitize(title)
                if not safe_title.lower().endswith(ext):
                    safe_title += ext

                if media_type == MEDIA_TYPE_NOTE:
                    save_path = os.path.join(self.kb_dir, item.get("relative_path", ""), safe_title)
                else:
                    save_path = os.path.join(self.kb_dir, item.get("relative_path", ""), safe_title)

                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    skipped += 1
                    self.after(0, self._update_stat, self.stat_skipped, skipped)
                    continue

                if not jump_url:
                    skipped += 1
                    self.after(0, self._update_stat, self.stat_skipped, skipped)
                    continue

                self.after(0, self._update_progress, i + 1, total, f"[{i + 1}/{total}] {title[:55]}")
                self.after(0, self._log, f"[{i + 1}/{total}] {title}")

                try:
                    r = requests.get(jump_url, timeout=60, stream=True)
                    if r.status_code == 200:
                        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
                        with open(save_path, "wb") as fobj:
                            for chunk in r.iter_content(8192):
                                if self.cancel_flag:
                                    break
                                fobj.write(chunk)
                        size = os.path.getsize(save_path)
                        downloaded += 1
                        self.after(0, self._update_stat, self.stat_downloaded, downloaded)
                        self.after(0, self._log, f"  -> OK ({size} bytes)")
                    else:
                        failed += 1
                        self.after(0, self._update_stat, self.stat_failed, failed)
                        self.after(0, self._log, f"  -> HTTP {r.status_code}")
                except Exception as e:
                    failed += 1
                    self.after(0, self._update_stat, self.stat_failed, failed)
                    self.after(0, self._log, f"  -> Error: {str(e)[:80]}")

            self.after(0, self._update_progress, total, total, "Complete!")
            self.after(0, self._log, "")
            self.after(0, self._log, f"Done! Downloaded: {downloaded}, Failed: {failed}, Skipped: {skipped}")

        except Exception as e:
            self.after(0, self._log, f"ERROR: {e}")

        finally:
            self.after(0, self._set_state)

    def _extract_share_id(self, url):
        if "shareId=" in url:
            return url.split("shareId=")[1].split("&")[0]
        return url

    def _is_valid_hex(self, sid):
        return len(sid) == 64 and all(c in "0123456789abcdef" for c in sid.lower())

    def _find_valid_share_id(self, bad_id):
        if self._is_valid_hex(bad_id):
            return [bad_id]
        non_hex = [i for i, c in enumerate(bad_id.lower()) if c not in "0123456789abcdef"]
        if len(non_hex) != 1 or len(bad_id) != 64:
            return [bad_id]
        pos = non_hex[0]
        return [bad_id[:pos] + c + bad_id[pos + 1:] for c in "0123456789abcdef"]

    def _api_get_share_info(self, share_id, folder_id=None):
        payload = {"shareId": share_id, "limit": PAGE_SIZE}
        if folder_id:
            payload["folder_id"] = folder_id
        try:
            r = requests.post(API_BASE, json=payload, timeout=15)
            d = r.json()
            if d.get("code") == 0:
                return d
        except Exception:
            pass
        return None

    def _sanitize(self, name):
        name = re.sub(r'[\\/:*?"<>|]', "_", name)
        return name.strip(". ")[:200] or "unnamed"

    def _get_file_ext(self, title, url):
        ext_map = {".pdf": ".pdf", ".doc": ".doc", ".docx": ".docx", ".xls": ".xls",
                   ".xlsx": ".xlsx", ".ppt": ".ppt", ".pptx": ".pptx",
                   ".jpg": ".jpg", ".png": ".png", ".dwg": ".dwg"}
        lower = title.lower()
        for s, e in ext_map.items():
            if lower.endswith(s):
                return e
        if url:
            up = url.split("?")[0].lower()
            for s, e in ext_map.items():
                if up.endswith(s):
                    return e
        return ".bin"


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    app = macOSApp()
    app.mainloop()
