;;; ============================================================
;;; PDSG-LISP 图形界面模块
;;; 使用 DCL 创建精美的主界面
;;; ============================================================

;;; ------------------------------------------------------------
;;; 全局 UI 变量
;;; ------------------------------------------------------------
(setq *pdsg-ui-file* nil)
(setq *pdsg-ui-sheet* nil)
(setq *pdsg-ui-source-type* 1)  ; 1=Excel, 2=CSV
(setq *pdsg-ui-paper-size* "A3")
(setq *pdsg-ui-bus-y* "220")
(setq *pdsg-ui-spacing* "35")
(setq *pdsg-ui-start-x* "20")
(setq *pdsg-ui-output-dir* nil)
(setq *pdsg-ui-output-name* "配电系统图")
(setq *pdsg-ui-auto-save* 1)
(setq *pdsg-ui-use-std-blocks* 1)
(setq *pdsg-ui-create-missing* 1)
(setq *pdsg-ui-block-scale* "1.0")
(setq *pdsg-ui-block-rotation* "0")
(setq *pdsg-ui-record-count* 0)

;;; ------------------------------------------------------------
;;; 获取 DCL 文件路径
;;; ------------------------------------------------------------
(defun pdsg-get-dcl-path ()
  (if (and *pdsg-install-dir* (/= *pdsg-install-dir* ""))
    (strcat *pdsg-install-dir* "pdsg-dialog.dcl")
    "pdsg-dialog.dcl"
  )
)

;;; ------------------------------------------------------------
;;; 显示主界面
;;; ------------------------------------------------------------
(defun c:PDSG_UI ( / dcl-id result file-list dcl-file
                     old-cmdecho old-osmode old-clayer old-error)
  (setq old-cmdecho (getvar "cmdecho")
        old-osmode (getvar "osmode")
        old-clayer (getvar "clayer")
        old-error *error*)
  (setvar "cmdecho" 0)
  (defun *error* (msg)
    (setq *error* old-error)
    (setvar "cmdecho" old-cmdecho)
    (setvar "osmode" old-osmode)
    (setvar "clayer" old-clayer)
    (if msg (princ (strcat "\n[ERROR] " (vl-princ-to-string msg))))
    (princ))
  (setq dcl-file (pdsg-get-dcl-path))

  ;; 检查 DCL 文件
  (if (null (findfile dcl-file))
    (progn
      (princ (strcat "\n[ERROR] 未找到 DCL 文件: " dcl-file))
      (princ "\n请将 pdsg-dialog.dcl 复制到 AutoCAD 支持路径")
    )
    (progn
      (setq dcl-id (load_dialog dcl-file))
      (if (< dcl-id 0)
        (princ "\n[ERROR] 无法加载 DCL 文件")
        (progn
          (if (new_dialog "pdsg_main" dcl-id)
            (progn
              (set_tile "version" "v1.0.0")
              (set_tile "file_path" (if *pdsg-ui-file* *pdsg-ui-file* ""))
              (set_tile "sheet_name" (if *pdsg-ui-sheet* *pdsg-ui-sheet* ""))
              (set_tile "bus_y" *pdsg-ui-bus-y*)
              (set_tile "spacing" *pdsg-ui-spacing*)
              (set_tile "start_x" *pdsg-ui-start-x*)
              (set_tile "output_name" *pdsg-ui-output-name*)
              (set_tile "status" "就绪")
              (set_tile "record_count" (strcat "记录: " (itoa *pdsg-ui-record-count*)))

              (action_tile "browse_btn" "(pdsg-browse-file)")
              (action_tile "output_browse" "(pdsg-browse-output)")
              (action_tile "preview" "(pdsg-preview-data)")
              (action_tile "dry_run" "(pdsg-dry-run)")
              (action_tile "generate" "(pdsg-generate)")
              (action_tile "cancel" "(done_dialog 0)")

              (setq result (start_dialog))

              (if (= result 0)
                (princ "\n[INFO] 已取消")
              )
            )
            (princ "\n[ERROR] 无法显示对话框")
          )
          (unload_dialog dcl-id)
        )
      )
    )
  )
  (setq *error* old-error)
  (setvar "cmdecho" old-cmdecho)
  (setvar "osmode" old-osmode)
  (setvar "clayer" old-clayer)
  (princ)
)

;;; ------------------------------------------------------------
;;; 浏览文件
;;; ------------------------------------------------------------
(defun pdsg-browse-file (/ file ext)
  (setq ext (nth (atoi (get_tile "data_source")) '("xls;xlsx" "csv")))
  (setq file (getfile "选择数据文件" ext "选择"))

  (if file
    (progn
      (setq *pdsg-ui-file* file)
      (set_tile "file_path" file)
      (set_tile "status" (strcat "已选择: " (filename-only file)))

      ;; 自动检测工作表
      (if (= (atoi (get_tile "data_source")) 0)
        (progn
          (set_tile "sheet_name" "")
          (set_tile "status" "Excel 文件已选择")
        )
        (progn
          (set_tile "sheet_name" "N/A")
          (set_tile "status" "CSV 文件已选择")
        )
      )
    )
  )
)

;;; ------------------------------------------------------------
;;; 浏览输出目录
;;; ------------------------------------------------------------
(defun pdsg-browse-output (/ dir)
  (setq dir (getvar "DWGPREFIX"))
  (if (or (null dir) (= dir ""))
    (setq dir (getvar "TEMPPREFIX"))
  )

  (setq dir (LM_BrowseForFolder "" dir 0))

  (if dir
    (progn
      (setq *pdsg-ui-output-dir* dir)
      (set_tile "output_path" dir)
      (set_tile "status" (strcat "输出目录: " dir))
    )
  )
)

;;; ------------------------------------------------------------
;;; 浏览文件夹辅助函数
;;; ------------------------------------------------------------
(defun LM_BrowseForFolder ( msg shfolder flags / ShellFolder result path pidl )
  (if (setq ShellFolder (vlax-create-object "Shell.Application"))
    (progn
      (setq result (vlax-invoke-method ShellFolder 'BrowseForFolder 0 msg flags shfolder))
      (if result
        (progn
          (setq pidl (vlax-get-property result 'Self))
          (setq path (vlax-get-property pidl 'Path))
          (vlax-release-object result)
          (vlax-release-object ShellFolder)
          (if (and path (/= path ""))
            (vl-string-translate "/" "\\" path)
            nil
          )
        )
        (progn
          (vlax-release-object ShellFolder)
          nil
        )
      )
    )
    nil
  )
)

;;; ------------------------------------------------------------
;;; 辅助函数：获取文件名
;;; ------------------------------------------------------------
(defun filename-only (filepath / pos result)
  (setq result filepath)
  (setq pos (vl-string-search "\\" filepath))
  (while pos
    (setq result (substr filepath (+ pos 2)))
    (setq pos (vl-string-search "\\" filepath (+ pos 1)))
  )
  result
)

;;; ------------------------------------------------------------
;;; 预览数据
;;; ------------------------------------------------------------
(defun pdsg-preview-data (/ records dcl-id result preview-str i dcl-file)
  (if (null *pdsg-ui-file*)
    (alert "请先选择数据文件")
    (progn
      (set_tile "status" "正在读取数据...")

      ;; 读取数据
      (if (= (atoi (get_tile "data_source")) 0)
        (setq records (pdsg-read-excel *pdsg-ui-file* *pdsg-ui-sheet*))
        (setq records (pdsg-read-csv *pdsg-ui-file*))
      )

      (if (and records (> (length records) 0))
        (progn
          (setq *pdsg-ui-record-count* (length records))
          (set_tile "record_count" (strcat "记录: " (itoa (length records))))

          ;; 构建预览字符串（最多显示20条）
          (setq preview-str "")
          (setq i 0)
          (foreach rec records
            (if (< i 20)
              (progn
                (setq preview-str
                  (strcat preview-str
                    (itoa (1+ i)) ". "
                    (cdr (assoc "circuit_name" rec))
                    " | "
                    (cdr (assoc "breaker_type" rec))
                    " | "
                    (cdr (assoc "breaker_rating" rec))
                    "\n"
                  )
                )
                (setq i (1+ i))
              )
            )
          )

          (if (> (length records) 20)
            (setq preview-str (strcat preview-str "\n... 还有 " (itoa (- (length records) 20)) " 条记录"))
          )

          ;; 显示预览对话框（使用 let 绑定 dcl-id 并确保释放）
          (let ((preview-dcl (load_dialog (pdsg-get-dcl-path))))
            (if (and preview-dcl (new_dialog "pdsg_preview" preview-dcl))
              (progn
                (set_tile "preview_title" (strcat "数据预览 - " (itoa (length records)) " 条记录"))
                (set_tile "preview_list" preview-str)
                (set_tile "preview_info" (strcat "共 " (itoa (length records)) " 条有效记录"))
                (start_dialog)
              )
            )
            (if preview-dcl (unload_dialog preview-dcl))
          )

          (set_tile "status" (strcat "预览完成: " (itoa (length records)) " 条记录"))
        )
        (progn
          (alert "未读取到有效数据")
          (set_tile "status" "读取失败")
        )
      )
    )
  )
)

;;; ------------------------------------------------------------
;;; 校验数据（干运行）
;;; ------------------------------------------------------------
;;; 校验数据（干运行）
;;; ------------------------------------------------------------
(defun pdsg-dry-run (/ records valid-errors valid errors error-str dcl-id dcl-file)
  (if (null *pdsg-ui-file*)
    (alert "请先选择数据文件")
    (progn
      (set_tile "status" "正在校验数据...")

      ;; 读取数据
      (if (= (atoi (get_tile "data_source")) 0)
        (setq records (pdsg-read-excel *pdsg-ui-file* *pdsg-ui-sheet*))
        (setq records (pdsg-read-csv *pdsg-ui-file*))
      )

      (if (and records (> (length records) 0))
        (progn
          (setq *pdsg-ui-record-count* (length records))
          (set_tile "record_count" (strcat "记录: " (itoa (length records))))

          ;; 校验
          (setq valid-errors (pdsg-validate-records records))
          (setq valid (car valid-errors))
          (setq errors (cadr valid-errors))

          (if (> (length errors) 0)
            (progn
              ;; 构建错误列表
              (setq error-str "")
              (foreach err errors
                (setq error-str (strcat error-str "第 " (itoa (car err)) " 行: " (cdr err) "\n"))
              )

          ;; 显示错误对话框
          (let ((error-dcl (load_dialog (pdsg-get-dcl-path))))
            (if (and error-dcl (new_dialog "pdsg_errors" error-dcl))
              (progn
                (set_tile "error_title" (strcat "数据校验错误 (" (itoa (length errors)) " 个)"))
                (set_tile "error_list" error-str)
                (set_tile "error_summary" (strcat "有效: " (itoa (length valid)) " / 错误: " (itoa (length errors))))
                (start_dialog)
              )
            )
            (if error-dcl (unload_dialog error-dcl))
          )

              (set_tile "status" (strcat "校验完成: " (itoa (length errors)) " 个错误"))
            )
            (progn
              (alert (strcat "校验通过!\n\n有效回路: " (itoa (length valid)) "\n\n可以生成配电系统图"))
              (set_tile "status" (strcat "校验通过: " (itoa (length valid)) " 条有效记录"))
            )
          )
        )
        (progn
          (alert "未读取到有效数据")
          (set_tile "status" "读取失败")
        )
      )
    )
  )
)

;;; ------------------------------------------------------------
;;; 生成配电系统图
;;; ------------------------------------------------------------
(defun pdsg-generate (/ records valid-errors valid errors
                        paper-width paper-height bus-y spacing start-x
                        placements output-path paper-map
                        old-cmdecho old-osmode old-clayer old-error)
  (setq old-cmdecho (getvar "cmdecho")
        old-osmode (getvar "osmode")
        old-clayer (getvar "clayer")
        old-error *error*)
  (setvar "cmdecho" 0)
  (defun *error* (msg)
    (setq *error* old-error)
    (setvar "cmdecho" old-cmdecho)
    (setvar "osmode" old-osmode)
    (setvar "clayer" old-clayer)
    (set_tile "status" (strcat "错误: " (if msg (vl-princ-to-string msg) "未知错误")))
    (princ (strcat "\n[ERROR] " (if msg (vl-princ-to-string msg) "未知错误")))
    (princ))
  (if (null *pdsg-ui-file*)
    (alert "请先选择数据文件")
    (progn
      (set_tile "status" "正在生成配电系统图...")

      ;; 读取数据
      (if (= (atoi (get_tile "data_source")) 0)
        (setq records (pdsg-read-excel *pdsg-ui-file* *pdsg-ui-sheet*))
        (setq records (pdsg-read-csv *pdsg-ui-file*))
      )

      (if (and records (> (length records) 0))
        (progn
          (setq *pdsg-ui-record-count* (length records))

          ;; 校验
          (setq valid-errors (pdsg-validate-records records))
          (setq valid (car valid-errors))
          (setq errors (cadr valid-errors))

          (if (> (length valid) 0)
            (progn
              ;; 获取图纸参数（使用关联列表映射）
              (setq paper-map (list
                (cons "0" (list 420.0 297.0))
                (cons "1" (list 594.0 420.0))
                (cons "2" (list 841.0 594.0))
                (cons "3" (list 1189.0 841.0))
              ))
              (setq paper-width (car (cdr (assoc (get_tile "paper_size") paper-map))))
              (setq paper-height (cadr (cdr (assoc (get_tile "paper_size") paper-map))))
              (setq bus-y (atof *pdsg-ui-bus-y*))
              (setq spacing (atof *pdsg-ui-spacing*))
              (setq start-x (atof *pdsg-ui-start-x*))

              ;; 计算布局
              (setq placements (pdsg-compute-layout valid paper-width paper-height
                                                    bus-y spacing start-x))

              ;; 开始绘制
              (command "_.UNDO" "_Begin")

              ;; 初始化绘图环境
              (pdsg-init-drawing)

              ;; 绘制母线
              (pdsg-draw-bus start-x (+ start-x (* spacing (1- (length valid))))
                             bus-y "BUS" 1 50)

              ;; 绘制回路图块
              (pdsg-draw-placements placements)

              ;; 绘制图框
              (pdsg-draw-frame paper-width paper-height "配电系统图" "")

              (command "_.UNDO" "_End")

              ;; 自动保存
              (if (= *pdsg-ui-auto-save* 1)
                (progn
                  (setq output-path (strcat (getvar "DWGPREFIX")
                                            *pdsg-ui-output-name* ".dwg"))
                  (command "_.SAVEAS" output-path)
                  (set_tile "status" (strcat "生成完成并保存: " output-path))
                )
                (set_tile "status" (strcat "生成完成: " (itoa (length valid)) " 个回路"))
              )

              (princ (strcat "\n[DONE] 生成完成: " (itoa (length valid)) " 个回路"))
            )
            (progn
              (alert "无有效回路数据")
              (set_tile "status" "生成失败: 无有效数据")
            )
          )
        )
        (progn
          (alert "未读取到有效数据")
          (set_tile "status" "读取失败")
        )
      )
    )
  )
  (setq *error* old-error)
  (setvar "cmdecho" old-cmdecho)
  (setvar "osmode" old-osmode)
  (setvar "clayer" old-clayer)
)

;;; ------------------------------------------------------------
;;; 关于对话框
;;; ------------------------------------------------------------
(defun c:PDSG_ABOUT ( / dcl-id dcl-file)
  (setq dcl-file (pdsg-get-dcl-path))
  (if (null (findfile dcl-file))
    (princ "\n[ERROR] 未找到 DCL 文件")
    (progn
      (setq dcl-id (load_dialog dcl-file))
      (if (new_dialog "pdsg_about" dcl-id)
        (progn
          (set_tile "about_version" (strcat "版本: " *pdsg-version*))
          (start_dialog)
        )
      )
      (unload_dialog dcl-id)
    )
  )
  (princ)
)

(princ "\n[PDSG-LISP 界面模块已加载]")
