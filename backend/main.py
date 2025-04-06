from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import xmind
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import tempfile
import shutil
import re

# 加载环境变量
load_dotenv()

app = FastAPI(title="AI测试用例分析系统")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TestCaseAnalyzer:
    def __init__(self):
        # 定义关键词列表
        self.completeness_keywords = ['前置条件', '步骤', '预期结果', '实际结果']
        self.coverage_keywords = ['功能测试', '性能测试', '安全测试', '兼容性测试', '界面测试']
        
    def analyze_test_cases(self, test_cases):
        try:
            # 将测试用例转换为字符串格式
            test_cases_str = json.dumps(test_cases, ensure_ascii=False, indent=2)
            
            # 分析测试用例
            completeness = self._analyze_completeness(test_cases)
            duplication = self._analyze_duplication(test_cases)
            coverage = self._analyze_coverage(test_cases)
            suggestions = self._generate_suggestions(test_cases, completeness, duplication, coverage)
            
            analysis_result = {
                "completeness": completeness,
                "duplication": duplication,
                "coverage": coverage,
                "suggestions": suggestions
            }
            
            return analysis_result
            
        except Exception as e:
            print(f"分析过程出错: {str(e)}")
            raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
    
    def _analyze_completeness(self, test_cases):
        """分析测试用例完整性"""
        total_score = 0
        for test_case in test_cases:
            case_text = test_case['path'].lower() + ' ' + test_case['title'].lower()
            keyword_count = sum(1 for keyword in self.completeness_keywords if keyword in case_text)
            case_score = (keyword_count / len(self.completeness_keywords)) * 100
            total_score += case_score
        
        return int(total_score / len(test_cases)) if test_cases else 50
    
    def _analyze_duplication(self, test_cases):
        """分析测试用例重复度"""
        titles = [case['title'] for case in test_cases]
        paths = [case['path'] for case in test_cases]
        
        # 计算重复的标题数量
        duplicate_titles = len(titles) - len(set(titles))
        # 计算重复的路径数量
        duplicate_paths = len(paths) - len(set(paths))
        
        # 计算重复率
        duplication_rate = ((duplicate_titles + duplicate_paths) / (len(test_cases) * 2)) * 100
        return int(duplication_rate)
    
    def _analyze_coverage(self, test_cases):
        """分析测试覆盖度"""
        covered_types = set()
        for test_case in test_cases:
            case_text = test_case['path'].lower() + ' ' + test_case['title'].lower()
            for keyword in self.coverage_keywords:
                if keyword in case_text:
                    covered_types.add(keyword)
        
        coverage_rate = (len(covered_types) / len(self.coverage_keywords)) * 100
        return int(coverage_rate)
    
    def _generate_suggestions(self, test_cases, completeness, duplication, coverage):
        """生成优化建议"""
        suggestions = []
        
        if completeness < 70:
            suggestions.append("建议完善测试用例的基本要素，包括前置条件、测试步骤和预期结果")
        
        if duplication > 30:
            suggestions.append("存在较多重复的测试用例，建议合并或删除重复项")
        
        if coverage < 60:
            suggestions.append("测试覆盖度不足，建议增加不同类型的测试用例")
        
        if len(test_cases) < 5:
            suggestions.append("测试用例数量较少，建议增加更多测试场景")
        
        if not suggestions:
            suggestions.append("测试用例质量良好，建议持续维护和更新")
        
        return suggestions

analyzer = TestCaseAnalyzer()

@app.post("/api/upload")
async def upload_xmind(file: UploadFile = File(...)):
    if not file.filename.endswith('.xmind'):
        raise HTTPException(status_code=400, detail="只支持上传.xmind文件")
    
    try:
        print(f"接收到文件: {file.filename}")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, file.filename)
            
            # 以二进制模式保存上传的文件
            with open(temp_file_path, 'wb') as temp_file:
                shutil.copyfileobj(file.file, temp_file)
            
            try:
                # 解析XMind文件
                workbook = xmind.load(temp_file_path)
                sheet = workbook.getPrimarySheet()
                if not sheet:
                    raise ValueError("无法读取XMind文件的主工作表")
                
                root_topic = sheet.getRootTopic()
                if not root_topic:
                    raise ValueError("无法读取XMind文件的根主题")
                
                # 提取测试用例信息
                test_cases = extract_test_cases(root_topic)
                
                if not test_cases:
                    return JSONResponse(content={
                        "status": "error",
                        "message": "未找到有效的测试用例",
                        "data": None
                    })
                
                # 分析测试用例
                analysis_result = analyzer.analyze_test_cases(test_cases)
                
                return JSONResponse(content={
                    "status": "success",
                    "message": "文件分析完成",
                    "data": analysis_result,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"XMind文件处理错误: {str(e)}")
                raise HTTPException(status_code=500, detail=f"XMind文件处理失败: {str(e)}")
            
    except Exception as e:
        print(f"处理过程出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()

def extract_test_cases(topic):
    """递归提取XMind中的测试用例信息"""
    test_cases = []
    
    def traverse(node, path=[]):
        if not node:
            return
            
        title = node.getTitle()
        if not title:
            return
            
        current_path = path + [title]
        
        # 如果是叶子节点，认为是测试用例
        subtopics = node.getSubTopics()
        if not subtopics:
            test_cases.append({
                "path": " -> ".join(current_path),
                "title": title
            })
        else:
            # 递归处理子节点
            for subtopic in subtopics:
                traverse(subtopic, current_path)
    
    traverse(topic)
    return test_cases

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")