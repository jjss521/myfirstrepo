;;; ============================================================
;;; PDSG-LISP - 配电系统图自动生成程序
;;; 转换自 PDSG.NET (C# → AutoLISP)
;;; 用于 AutoCAD 运行
;;; ============================================================

;;; 全局变量
(setq *pdsg-version* "1.0.0")
(setq *pdsg-config* nil)
(setq *pdsg-block-catalog* nil)

;;; 布局常量
(setq *pdsg-max-cols* 12)      ; 每行最大回路数
(setq *pdsg-row-height* 80.0)  ; 行间距 (mm)
(setq *pdsg-unit* "mm")        ; 坐标单位

;;; ------------------------------------------------------------
;;; 加载配置（支持简单 key: value 格式）
;;; ------------------------------------------------------------
(defun pdsg-load-config ( / config-file f line key val colon-pos)
  (setq config-file (findfile "pdsg-config.yaml"))
  (if (null config-file)
    (progn
      (princ "\n[WARN] 未找到配置文件 pdsg-config.yaml，使用默认配置")
      (pdsg-init-default-catalog)
      nil
    )
    (progn
      (setq *pdsg-config* (list))
      (setq f (open config-file "r"))
      (if (null f)
        (progn
          (princ (strcat "\n[WARN] 无法打开配置文件: " config-file))
          (pdsg-init-default-catalog)
          nil
        )
        (progn
          (vl-catch-all-apply
            (function (lambda ()
              (while (setq line (read-line f))
                (if (and (> (strlen line) 0) (/= (substr line 1 1) "#"))
                  (progn
                    (setq colon-pos (vl-string-search ":" line))
                    (if colon-pos
                      (progn
                        (setq key (vl-string-trim " " (substr line 1 colon-pos)))
                        (setq val (vl-string-trim " " (substr line (+ 2 colon-pos))))
                        (if (and key val (/= key ""))
                          (setq *pdsg-config* (append *pdsg-config* (list (cons key val))))
                        )
                      )
                    )
                  )
                )
              )
            ))
          )
          (close f)
          (princ (strcat "\n[INFO] 配置加载完成: " config-file))
          (pdsg-init-default-catalog)
          t
        )
      )
    )
  )
)

;;; ------------------------------------------------------------
;;; 初始化默认图块目录
;;; ------------------------------------------------------------
(defun pdsg-init-default-catalog ()
  (setq *pdsg-block-catalog*
    (list
      (cons "MCCB" "LOOP_MCCB")
      (cons "MCB" "LOOP_MCB")
      (cons "ACB" "LOOP_ACB")
      (cons "CONTACTOR" "LOOP_CONTACTOR")
      (cons "FUSE" "LOOP_FUSE")
      (cons "DEFAULT" "LOOP_DEFAULT")
    )
  )
  (princ "\n[INFO] 图块目录已初始化")
)

;;; ------------------------------------------------------------
;;; 读取 CSV 回路数据（替代 Excel 读取）
;;; CSV 编码: UTF-8，分隔符: 逗号
;;; ------------------------------------------------------------
(defun pdsg-read-csv (csv-file / f line records fields record row-num)
  (setq records (list))
  (setq row-num 0)
  (setq f (open csv-file "r"))
  (if (null f)
    (progn
      (princ (strcat "\n[ERROR] 无法打开文件: " csv-file))
      (list)
    )
    (progn
      ;; 跳过标题行
      (read-line f)
      (vl-catch-all-apply
        (function (lambda ()
          (while (setq line (read-line f))
            (setq row-num (1+ row-num))
            (if (> (strlen line) 0)
              (progn
                (setq fields (pdsg-split-csv-line line))
                (if (>= (length fields) 6)
                  (progn
                    (setq record
                      (list
                        (cons "row" row-num)
                        (cons "circuit_name" (nth 0 fields))
                        (cons "breaker_type" (nth 1 fields))
                        (cons "breaker_rating" (nth 2 fields))
                        (cons "cable_spec" (nth 3 fields))
                        (cons "cable_length" (nth 4 fields))
                        (cons "load_name" (nth 5 fields))
                        (if (> (length fields) 6) (cons "load_power" (nth 6 fields)) (cons "load_power" "0"))
                        (if (> (length fields) 7) (cons "load_current" (nth 7 fields)) (cons "load_current" "0"))
                      )
                    )
                    (setq records (append records (list record)))
                  )
                  (princ (strcat "\n[WARN] 第 " (itoa row-num) " 行字段不足，已跳过"))
                )
              )
            )
          )
        ))
      )
      (close f)
      (princ (strcat "\n[INFO] 读取 " (itoa (length records)) " 条回路记录"))
      records
    )
  )
)

;;; 安全版 nth — 越界时返回 nil 而非崩溃
(defun pdsg-nth (n lst / i val)
  (setq i 0)
  (setq val nil)
  (foreach item lst
    (if (= i n) (setq val item))
    (setq i (1+ i))
  )
  val
)

;;; CSV 行解析（支持带引号的字段）
(defun pdsg-split-csv-line (line / fields field in-quote i ch)
  (setq fields (list))
  (setq field "")
  (setq in-quote nil)
  (setq i 1)
  (while (<= i (strlen line))
    (setq ch (substr line i 1))
    (cond
      ((= ch "\"")
       (setq in-quote (not in-quote)))
      ((and (= ch ",") (not in-quote))
       (setq fields (append fields (list (vl-string-trim " " field))))
       (setq field ""))
      (T
       (setq field (strcat field ch)))
    )
    (setq i (1+ i))
  )
  (setq fields (append fields (list (vl-string-trim " " field))))
  fields
)

;;; ------------------------------------------------------------
;;; 回路数据校验
;;; ------------------------------------------------------------
(defun pdsg-validate-records (records / valid errors rec name breaker rating)
  (setq valid (list))
  (setq errors (list))
  (foreach rec records
    (setq name (cdr (assoc "circuit_name" rec)))
    (setq breaker (cdr (assoc "breaker_type" rec)))
    (setq rating (cdr (assoc "breaker_rating" rec)))
    (if (and name (/= name "") breaker (/= breaker "") rating (/= rating ""))
      (setq valid (append valid (list rec)))
      (setq errors (append errors (list (cons (cdr (assoc "row" rec)) "必要字段缺失"))))
    )
  )
  (princ (strcat "\n[INFO] 校验完成: 有效 " (itoa (length valid)) " / 跳过 " (itoa (length errors))))
  (list valid errors)
)

;;; ------------------------------------------------------------
;;; 图块映射
;;; ------------------------------------------------------------
(defun pdsg-map-circuit-to-block (record catalog / breaker-type block-name found)
  (setq breaker-type (strcase (cdr (assoc "breaker_type" record)))
        block-name nil
        found nil)
  (setq block-name nil)
  (setq found nil)
  (foreach item catalog
    (if (= breaker-type (strcase (cdr (assoc "type" item))))
      (progn
        (setq block-name (cdr (assoc "block_name" item)))
        (setq found t)
      )
    )
  )
  (if (null found)
    (progn
      (princ (strcat "\n[WARN] 未找到匹配图块: " breaker-type))
      (setq block-name "LOOP_DEFAULT")
    )
  )
  block-name
)

;;; ------------------------------------------------------------
;;; 属性构建
;;; ------------------------------------------------------------
(defun pdsg-build-attributes (record / attrs)
  (setq attrs (list))
  (setq attrs (append attrs (list (cons "CIRCUIT_NAME" (cdr (assoc "circuit_name" record))))))
  (setq attrs (append attrs (list (cons "BREAKER_TYPE" (cdr (assoc "breaker_type" record))))))
  (setq attrs (append attrs (list (cons "BREAKER_RATING" (cdr (assoc "breaker_rating" record))))))
  (setq attrs (append attrs (list (cons "CABLE_SPEC" (cdr (assoc "cable_spec" record))))))
  (setq attrs (append attrs (list (cons "CABLE_LENGTH" (cdr (assoc "cable_length" record))))))
  (setq attrs (append attrs (list (cons "LOAD_NAME" (cdr (assoc "load_name" record))))))
  (setq attrs (append attrs (list (cons "LOAD_POWER" (cdr (assoc "load_power" record))))))
  (setq attrs (append attrs (list (cons "LOAD_CURRENT" (cdr (assoc "load_current" record))))))
  attrs
)

;;; ------------------------------------------------------------
;;; 布局计算
;;; ------------------------------------------------------------
(defun pdsg-compute-layout (records paper-width paper-height bus-y spacing start-x
                            / placements x y col row block-name attrs ent)
  (setq placements (list))
  (setq x start-x)
  (setq y bus-y)
  (setq col 0)
  (setq row 0)

  (foreach rec records
    (setq block-name (pdsg-map-circuit-to-block rec *pdsg-block-catalog*))
    (setq attrs (pdsg-build-attributes rec))

    (setq placements
      (append placements
        (list
          (list
            (cons "block_name" block-name)
            (cons "attributes" attrs)
            (cons "position" (list x y))
          )
        )
      )
    )

    (setq x (+ x spacing))
    (setq col (1+ col))

    ;; 每行超过最大列数时换行
    (if (> col *pdsg-max-cols*)
      (progn
        (setq col 0)
        (setq row (1+ row))
        (setq x start-x)
        (setq y (- y *pdsg-row-height*))
      )
    )
  )

  (princ (strcat "\n[INFO] 布局计算完成: " (itoa (length placements)) " 个回路"))
  placements
)

;;; ------------------------------------------------------------
;;; 绘制母线
;;; ------------------------------------------------------------
(defun pdsg-draw-bus-line (x-start x-end y / pt1 pt2)
  (setq pt1 (list x-start y 0.0))
  (setq pt2 (list x-end y 0.0))
  (command "_.LINE" pt1 pt2 "")
  (princ (strcat "\n[INFO] 绘制母线: (" (rtos x-start 2 1) "," (rtos y 2 1) ") ~ ("
                 (rtos x-end 2 1) "," (rtos y 2 1) ")"))
)

;;; ------------------------------------------------------------
;;; 绘制回路图块
;;; ------------------------------------------------------------
(defun pdsg-draw-placements (placements / p block-name attrs pos ent sub-ent ent-ent)
  (foreach p placements
    (setq block-name (cdr (assoc "block_name" p)))
    (setq attrs (cdr (assoc "attributes" p)))
    (setq pos (cdr (assoc "position" p)))

    ;; 插入图块
    (vl-catch-all-apply
      (function (lambda ()
        (command "_.INSERT" block-name pos 1.0 1.0 0.0)
      ))
    )

    ;; 获取刚插入的图块实体
    (setq ent (entlast))

    ;; 使用 entmod 直接修改属性
    (if (and ent attrs)
      (progn
        (setq sub-ent (entnext ent))
        (while sub-ent
          (setq ent-ent (entget sub-ent))
          (if (= (cdr (assoc 0 ent-ent)) "ATTRIB")
            (progn
              (foreach attr attrs
                (if (= (cdr (assoc 2 ent-ent)) (car attr))
                  (progn
                    (entmod (subst (cons 1 (cdr attr)) (assoc 1 ent-ent) ent-ent))
                    (entupd sub-ent)  ;; 修复：传实体名而非 DXF 列表
                  )
                )
              )
            )
          )
          (setq sub-ent (entnext sub-ent))
        )
      )
    )
  )
  (princ (strcat "\n[INFO] 绘制完成: " (itoa (length placements)) " 个图块"))
)

;;; ------------------------------------------------------------
;;; 绘制图框
;;; ------------------------------------------------------------
(defun pdsg-draw-title-block (paper-width paper-height title / x y w h)
  (setq w paper-width)
  (setq h paper-height)
  (setq x 0.0)
  (setq y 0.0)

  ;; 外框
  (command "_.RECTANGLE" (list x y) (list w h))

  ;; 标题栏区域（右下角）
  (setq tw 180)
  (setq th 56)
  (command "_.RECTANGLE" (list (- w tw) y) (list w th))

  ;; 分隔线
  (command "_.LINE" (list (- w tw) th) (list w th) "")
  (command "_.LINE" (list (- w 60) y) (list (- w 60) th) "")

  ;; 标题文字
  (command "_.TEXT" "MC" (list (- w 120) (/ th 2.0)) 5.0 0.0 title)
  (command "_.TEXT" "MC" (list (- w 30) (/ th 2.0)) 3.0 0.0 "配电系统图")

  (princ "\n[INFO] 图框绘制完成")
)

;;; ------------------------------------------------------------
;;; 主命令：PDSG - 生成配电系统图
;;; ------------------------------------------------------------
(defun c:PDSG ( / csv-file result records valid-errors valid errors
                    paper-width paper-height bus-y spacing start-x
                    placements cfg old-cmdecho old-osmode old-clayer old-error)
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
  (princ "\n")
  (princ "========================================")
  (princ "\n  PDSG 配电系统图自动生成")
  (princ (strcat "\n  版本: " *pdsg-version*))
  (princ "\n========================================")

  (pdsg-load-config)

  (setq csv-file (getfile "选择回路数据 CSV 文件" "CSV" "选择"))
  (if (null csv-file)
    (princ "\n[INFO] 已取消")
    (progn
      (setq records (pdsg-read-csv csv-file))
      (if (= (length records) 0)
        (princ "\n[ERROR] 无有效回路数据")
        (progn
          (setq valid-errors (pdsg-validate-records records))
          (setq valid (car valid-errors))
          (setq errors (cadr valid-errors))

          (if (> (length valid) 0)
            (progn
              (setq paper-width 420.0)
              (setq paper-height 297.0)
              (setq bus-y 220.0)
              (setq spacing 35.0)
              (setq start-x 20.0)

              (setq placements (pdsg-compute-layout valid paper-width paper-height
                                                    bus-y spacing start-x))

              (command "_.UNDO" "_Begin")

              (pdsg-draw-bus-line start-x
                                  (+ start-x (* spacing (1- (length valid))))
                                  bus-y)

              (pdsg-draw-placements placements)

              (pdsg-draw-title-block paper-width paper-height "配电系统图")

              (command "_.UNDO" "_End")

              (princ (strcat "\n\n[DONE] 生成完成: " (itoa (length valid)) " 个回路"))
              (princ "\n[DONE] 如需保存请使用 SAVE 命令")
            )
            (princ "\n[ERROR] 无有效回路数据")
          )
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
;;; 辅助命令：PDSG_DRY - 校验模式（不绘图）
;;; ------------------------------------------------------------
(defun c:PDSG_DRY ( / csv-file records valid-errors valid errors
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
  (princ "\n[PDSG_DRY] 校验模式 - 仅检查数据")

  (pdsg-load-config)

  (setq csv-file (getfile "选择回路数据 CSV 文件" "CSV" "选择"))
  (if (null csv-file)
    (progn
      (princ "\n[INFO] 已取消")
    )
    (progn
      (setq records (pdsg-read-csv csv-file))
      (setq valid-errors (pdsg-validate-records records))
      (setq valid (car valid-errors))
      (setq errors (cadr valid-errors))

      (princ "\n\n=== 校验结果 ===")
      (princ (strcat "\n有效回路: " (itoa (length valid))))
      (princ (strcat "\n错误记录: " (itoa (length errors))))

      (if (> (length errors) 0)
        (progn
          (princ "\n\n错误详情:")
          (foreach err errors
            (princ (strcat "\n  第 " (itoa (car err)) " 行: " (cdr err)))
          )
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
;;; 辅助命令：PDSG_BLOCKS - 列出图块
;;; ------------------------------------------------------------
(defun c:PDSG_BLOCKS ( / blist i)
  (princ "\n=== 当前图形中的图块 ===")
  (setq blist (tblnext "BLOCK" T))
  (setq i 0)
  (while blist
    (setq i (1+ i))
    (princ (strcat "\n  " (cdr (assoc 2 blist))))
    (setq blist (tblnext "BLOCK"))
  )
  (princ (strcat "\n共 " (itoa i) " 个图块"))
  (princ)
)

;;; ------------------------------------------------------------
;;; 辅助命令：PDSG_INFO - 显示版本信息
;;; ------------------------------------------------------------
(defun c:PDSG_INFO ()
  (princ (strcat "\nPDSG-LISP v" *pdsg-version*))
  (princ "\n配电系统图自动生成程序")
  (princ "\n转换自 PDSG.NET (C# → AutoLISP)")
  (princ (strcat "\n坐标单位: " *pdsg-unit*))
  (princ "\n")
  (princ "\n可用命令:")
  (princ "\n  PDSG        - 生成配电系统图")
  (princ "\n  PDSG_DRY    - 仅校验数据")
  (princ "\n  PDSG_BLOCKS - 列出图块")
  (princ "\n  PDSG_BCREATE - 创建新回路图块")
  (princ "\n  PDSG_BLIST  - 列出回路图块")
  (princ "\n  PDSG_BSTD   - 创建标准图块集合")
  (princ "\n  PDSG_BDIAG  - 诊断图块信息")
  (princ "\n  PDSG_INIT   - 加载所有模块")
  (princ "\n  PDSG_INFO   - 显示版本信息")
  (princ)
)

;;; 加载提示
(princ (strcat "\n[PDSG-LISP v" *pdsg-version* " 已加载]"))
(princ "\n输入 PDSG_INFO 查看可用命令")
(princ)
