import React, { useState } from 'react';
import { Layout, Upload, Button, message, Card, Progress, List, Typography, Space } from 'antd';
import { UploadOutlined, DownloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import './App.css';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [optimizedFile, setOptimizedFile] = useState(null);

  const handleUpload = async (file) => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      console.log('开始上传文件...');
      const response = await axios.post('http://localhost:8000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000,
      });

      console.log('上传响应:', response.data);

      if (response.data.status === 'success') {
        setAnalysisResult(response.data.data);
        setOptimizedFile(response.data.optimized_file);
        message.success('文件分析完成');
      } else {
        message.error('分析失败: ' + response.data.message);
      }
    } catch (error) {
      console.error('上传错误:', error);
      if (error.response) {
        message.error(`上传失败: ${error.response.status} - ${error.response.data.detail || '未知错误'}`);
      } else if (error.request) {
        message.error('服务器无响应，请确保后端服务正在运行');
      } else {
        message.error('请求错误: ' + error.message);
      }
    } finally {
      setLoading(false);
    }
    return false;
  };

  const handleDownload = async () => {
    if (!optimizedFile) {
      message.error('没有可下载的文件');
      return;
    }

    try {
      const response = await axios.get(`http://localhost:8000/api/download/${optimizedFile}`, {
        responseType: 'blob'
      });

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', optimizedFile);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载错误:', error);
      message.error('文件下载失败');
    }
  };

  return (
    <Layout className="layout">
      <Header>
        <Title level={2} style={{ color: 'white', margin: '16px 0' }}>
          AI测试用例分析系统
        </Title>
      </Header>
      <Content style={{ padding: '50px' }}>
        <Card>
          <Space size="large">
            <Upload
              beforeUpload={handleUpload}
              accept=".xmind"
              showUploadList={false}
            >
              <Button
                type="primary"
                icon={<UploadOutlined />}
                loading={loading}
                size="large"
              >
                上传XMind测试用例文件
              </Button>
            </Upload>
            {optimizedFile && (
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                size="large"
                onClick={handleDownload}
              >
                下载优化建议
              </Button>
            )}
          </Space>
        </Card>

        {analysisResult && (
          <Card title="分析结果" style={{ marginTop: 20 }}>
            <div style={{ marginBottom: 20 }}>
              <Title level={4}>测试用例质量评分</Title>
              <Progress
                type="circle"
                percent={analysisResult.completeness}
                format={percent => `完整性 ${percent}%`}
                style={{ marginRight: 20 }}
              />
              <Progress
                type="circle"
                percent={100 - analysisResult.duplication}
                format={percent => `重复度 ${100 - percent}%`}
                style={{ marginRight: 20 }}
              />
              <Progress
                type="circle"
                percent={analysisResult.coverage}
                format={percent => `覆盖度 ${percent}%`}
              />
            </div>

            <Title level={4}>优化建议</Title>
            <List
              dataSource={analysisResult.suggestions}
              renderItem={item => (
                <List.Item>
                  <Text>{item}</Text>
                </List.Item>
              )}
            />
          </Card>
        )}
      </Content>
    </Layout>
  );
}

export default App; 