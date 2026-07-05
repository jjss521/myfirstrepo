;;; ============================================================
;;; PDSG-LISP 图块管理模块
;;; 处理回路图块的创建、编辑、验证
;;; ============================================================

;;; ------------------------------------------------------------
;;; 检查图块是否存在
;;; ------------------------------------------------------------
(defun pdsg-block-exists (block-name / blist)
  (setq blist (tblsearch "BLOCK" block-name))
  (if blist T nil)
)

;;; ------------------------------------------------------------
;;; 创建回路图块（带属性定义）
;;; 使用 entmake 避免嵌套 command 导致的 AutoCAD 崩溃
;;; ------------------------------------------------------------
(defun pdsg-create-circuit-block (block-name description width height
                                    / pt1 pt2)
  (if (pdsg-block-exists block-name)
    (progn
      (princ (strcat "\n[WARN] 图块已存在: " block-name))
      nil
    )
    (progn
      ;; 使用 entmake 创建图块定义
      (entmake (list '(0 . "BLOCK") (cons 2 block-name) '(70 . 0) '(10 0.0 0.0 0.0)))

      ;; 矩形框（四条线段）
      (entmake (list '(0 . "LINE") (cons 10 (list 0.0 0.0 0.0)) (cons 11 (list width 0.0 0.0))))
      (entmake (list '(0 . "LINE") (cons 10 (list width 0.0 0.0)) (cons 11 (list width height 0.0))))
      (entmake (list '(0 . "LINE") (cons 10 (list width height 0.0)) (cons 11 (list 0.0 height 0.0))))
      (entmake (list '(0 . "LINE") (cons 10 (list 0.0 height 0.0)) (cons 11 (list 0.0 0.0 0.0))))

      ;; 断路器符号（简化）
      (entmake (list '(0 . "LINE")
                     (cons 10 (list (* width 0.3) (* height 0.4) 0.0))
                     (cons 11 (list (* width 0.7) (* height 0.4) 0.0))))
      (entmake (list '(0 . "LINE")
                     (cons 10 (list (* width 0.3) (* height 0.6) 0.0))
                     (cons 11 (list (* width 0.7) (* height 0.6) 0.0))))

      ;; 属性定义 — CIRCUIT_NAME
      (entmake (list
        '(0 . "ATTDEF") '(2 . "CIRCUIT_NAME") '(3 . "回路名称")
        '(70 . 0) '(1 . "") (cons 10 (list (* width 0.5) (* height 0.9) 0.0))
        (cons 11 (list (* width 0.5) (* height 0.9) 0.0))
        '(40 . 2.5) '(41 . 1.0) '(50 . 0.0) '(7 . "Standard")
        '(72 . 1) '(73 . 2)))

      ;; 属性定义 — BREAKER_TYPE
      (entmake (list
        '(0 . "ATTDEF") '(2 . "BREAKER_TYPE") '(3 . "断路器类型")
        '(70 . 0) '(1 . "") (cons 10 (list (* width 0.5) (* height 0.15) 0.0))
        (cons 11 (list (* width 0.5) (* height 0.15) 0.0))
        '(40 . 2.5) '(41 . 1.0) '(50 . 0.0) '(7 . "Standard")
        '(72 . 1) '(73 . 2)))

      ;; 属性定义 — BREAKER_RATING
      (entmake (list
        '(0 . "ATTDEF") '(2 . "BREAKER_RATING") '(3 . "额定电流")
        '(70 . 0) '(1 . "") (cons 10 (list (* width 0.5) (* height 0.05) 0.0))
        (cons 11 (list (* width 0.5) (* height 0.05) 0.0))
        '(40 . 2.5) '(41 . 1.0) '(50 . 0.0) '(7 . "Standard")
        '(72 . 1) '(73 . 2)))

      (entmake '((0 . "ENDBLK")))

      (princ (strcat "\n[INFO] 图块已创建: " block-name))
      T
    )
  )
)

;;; ------------------------------------------------------------
;;; 创建标准回路图块集合
;;; ------------------------------------------------------------
(defun pdsg-create-standard-blocks ( / blocks block-name desc width height)
  (setq blocks
    (list
      (list "LOOP_MCCB" "塑壳断路器回路" 30.0 60.0)
      (list "LOOP_MCB" "微型断路器回路" 25.0 50.0)
      (list "LOOP_ACB" "空气断路器回路" 35.0 70.0)
      (list "LOOP_CONTACTOR" "接触器回路" 30.0 60.0)
      (list "LOOP_FUSE" "熔断器回路" 25.0 50.0)
      (list "LOOP_DEFAULT" "默认回路" 30.0 60.0)
    )
  )

  (princ "\n=== 创建标准回路图块 ===")
  (foreach block blocks
    (setq block-name (nth 0 block))
    (setq desc (nth 1 block))
    (setq width (nth 2 block))
    (setq height (nth 3 block))
    (pdsg-create-circuit-block block-name desc width height)
  )
  (princ "\n[INFO] 标准图块创建完成")
)

;;; ------------------------------------------------------------
;;; 列出所有回路图块
;;; ------------------------------------------------------------
(defun pdsg-list-circuit-blocks ( / blist name prefix count)
  (princ "\n=== 回路图块列表 ===")
  (setq blist (tblnext "BLOCK" T))
  (setq count 0)
  (while blist
    (setq name (cdr (assoc 2 blist)))
    (if (= (substr name 1 5) "LOOP_")
      (progn
        (princ (strcat "\n  " name))
        (setq count (1+ count))
      )
    )
    (setq blist (tblnext "BLOCK"))
  )
  (princ (strcat "\n共 " (itoa count) " 个回路图块"))
  (princ)
)

;;; ------------------------------------------------------------
;;; 验证图块属性
;;; ------------------------------------------------------------
(defun pdsg-validate-block-attributes (block-name / ent attrs ent-attrs)
  (setq ent (tblobjname "BLOCK" block-name))
  (if (null ent)
    (progn
      (princ (strcat "\n[ERROR] 图块不存在: " block-name))
      nil
    )
    (progn
      (setq attrs (list))
      (while (setq ent (entnext ent))
        (if (= (cdr (assoc 0 (entget ent))) "ATTRIB")
          (setq attrs (append attrs (list (cdr (assoc 2 (entget ent))))))
        )
      )
      attrs
    )
  )
)

;;; ------------------------------------------------------------
;;; 导入外部图块
;;; ------------------------------------------------------------
(defun pdsg-import-blocks-from-dwg (dwg-path / count old-new)
  (if (null (findfile dwg-path))
    (progn
      (princ (strcat "\n[ERROR] 文件不存在: " dwg-path))
      0
    )
    (progn
      (princ (strcat "\n[INFO] 从 " dwg-path " 导入图块..."))
      ;; 使用 INSERT 命令导入
      (command "_.INSERT" dwg-path "0,0" 1.0 1.0 0.0)
      (command "_.ERASE" (entlast) "")
      (princ "\n[INFO] 图块导入完成")
      1
    )
  )
)

;;; ------------------------------------------------------------
;;; 诊断图块几何信息
;;; ------------------------------------------------------------
(defun pdsg-diagnose-blocks ( / blist name ent minpt maxpt width height)
  (princ "\n=== 图块诊断 ===")
  (setq blist (tblnext "BLOCK" T))
  (while blist
    (setq name (cdr (assoc 2 blist)))
    (if (= (substr name 1 5) "LOOP_")
      (progn
        (princ (strcat "\n图块: " name))
        ;; 这里可以添加更详细的诊断信息
        (princ " - 已定义")
      )
    )
    (setq blist (tblnext "BLOCK"))
  )
  (princ)
)

;;; ------------------------------------------------------------
;;; 图块管理命令
;;; ------------------------------------------------------------
(defun c:PDSG_BCREATE ( / block-name desc)
  (princ "\n[PDSG_BCREATE] 创建回路图块")
  (setq block-name (strcase (getstring T "\n请输入图块名称 (如 LOOP_POWER_C): ")))
  (if (= block-name "")
    (princ "\n[ERROR] 名称不能为空")
    (progn
      (setq desc (getstring T "\n请输入图块描述: "))
      (pdsg-create-circuit-block block-name desc 30.0 60.0)
    )
  )
  (princ)
)

(defun c:PDSG_BLIST ()
  (pdsg-list-circuit-blocks)
  (princ)
)

(defun c:PDSG_BDIAG ()
  (pdsg-diagnose-blocks)
  (princ)
)

(defun c:PDSG_BSTD ()
  (pdsg-create-standard-blocks)
  (princ)
)

(princ "\n[PDSG-LISP 图块模块已加载]")
