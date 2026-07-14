"""FastAPI 主程序"""
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime
import json

from .config import (
    UPLOAD_DIR, OUTPUT_DIR, ALLOWED_DOC_EXTENSIONS,
    DESIGN_STAGES, PROJECT_TYPES, RULES_DIR
)
from .database import get_db, init_db
from .models import ProjectType, Section, Template, Document, GenerationLog
from .schemas import (
    GenerateRequest, GenerateResponse,
    ProjectTypeOut, SectionOut, TemplateOut, DocumentOut
)
from .services.excel_parser import ExcelLoadParser
from .services.docx_generator import DocxGenerator

app = FastAPI(
    title='市政工程设计文件电气自控生成系统',
    version='0.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def startup():
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# === 工程类型 ===
@app.get('/api/project-types', response_model=list[ProjectTypeOut])
def list_project_types(db: Session = Depends(get_db)):
    return db.query(ProjectType).all()


# === 栏目 ===
@app.get('/api/sections', response_model=list[SectionOut])
def list_sections(
    project_type_id: int = None,
    db: Session = Depends(get_db)
):
    q = db.query(Section)
    if project_type_id:
        q = q.filter(Section.project_type_id == project_type_id)
    return q.order_by(Section.category, Section.section_order).all()


# === 文档管理 ===
@app.post('/api/documents/upload')
async def upload_document(
    file: UploadFile = File(...),
    project_type_id: int = Form(None),
    doc_type: str = Form('其他'),
    design_stage: str = Form('初步设计'),
    tags: str = Form('[]'),
    db: Session = Depends(get_db),
):
    """上传参考文档"""
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in ALLOWED_DOC_EXTENSIONS:
        raise HTTPException(400, f'不支持的文件类型: {ext}')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = f'{timestamp}_{file.filename}'
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    doc = Document(
        project_type_id=project_type_id,
        name=file.filename,
        file_path=file_path,
        doc_type=doc_type,
        design_stage=design_stage,
        file_ext=ext,
        file_size=len(content),
        tags=json.loads(tags),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {'id': doc.id, 'name': doc.name, 'message': '上传成功'}


@app.get('/api/documents', response_model=list[DocumentOut])
def list_documents(
    project_type_id: int = None,
    doc_type: str = None,
    db: Session = Depends(get_db)
):
    q = db.query(Document)
    if project_type_id:
        q = q.filter(Document.project_type_id == project_type_id)
    if doc_type:
        q = q.filter(Document.doc_type == doc_type)
    return q.order_by(Document.uploaded_at.desc()).all()


@app.delete('/api/documents/{doc_id}')
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).get(doc_id)
    if not doc:
        raise HTTPException(404, '文档不存在')
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return {'message': '已删除'}


# === 生成引擎 ===
@app.post('/api/generate', response_model=GenerateResponse)
async def generate_document(req: GenerateRequest, db: Session = Depends(get_db)):
    """根据负荷计算书生成电气自控设计文件"""
    try:
        # 1. 解析Excel
        if not os.path.exists(req.excel_path):
            raise HTTPException(400, f'文件不存在: {req.excel_path}')

        parser = ExcelLoadParser()
        excel_data = parser.parse(req.excel_path)

        # 2. 生成文档
        gen = DocxGenerator(rules_dir=RULES_DIR, output_dir=OUTPUT_DIR)
        params = {
            'project_name': req.project_name or '新建项目',
            'voltage_level': req.voltage_level or '10kV',
            'load_level': req.load_level or '二级',
            'project_type': req.project_type,
            'standby_power': req.standby_power,
        }
        output_path = gen.generate(req.project_type, req.design_stage, excel_data, params)

        # 3. 记录
        log = GenerationLog(
            project_type_id=None,
            design_stage=req.design_stage,
            input_file=req.excel_path,
            output_file=output_path,
            generation_params=params,
            excel_data={
                'total_power': excel_data['summary']['total_equip_power'],
                'total_sc': excel_data['summary']['total_sc_k'],
                'areas': len(excel_data.get('area_summaries', {})),
                'devices': excel_data['summary']['total_devices'],
            },
            status='success',
        )
        db.add(log)
        db.commit()

        return GenerateResponse(
            success=True,
            output_path=output_path,
            excel_summary=excel_data['summary'],
            message=f'生成成功！文件: {os.path.basename(output_path)}',
        )

    except Exception as e:
        return GenerateResponse(success=False, error=str(e))


@app.get('/api/generate/logs')
def list_generation_logs(db: Session = Depends(get_db)):
    return db.query(GenerationLog).order_by(GenerationLog.generated_at.desc()).limit(20).all()


# === 模板管理（预留） ===
@app.get('/api/templates', response_model=list[TemplateOut])
def list_templates(project_type_id: int = None, db: Session = Depends(get_db)):
    q = db.query(Template)
    if project_type_id:
        q = q.filter(Template.project_type_id == project_type_id)
    return q.order_by(Template.created_at.desc()).all()


# === 健康检查 ===
@app.get('/api/health')
def health():
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
