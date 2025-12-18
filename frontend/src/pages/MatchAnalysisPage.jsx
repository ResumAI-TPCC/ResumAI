/**
 * MatchAnalysisPage - 主页面
 * 
 * 布局: 三栏结构
 * - 左侧: Sidebar (输入区)
 * - 中间: MatchAnalysis (分析结果)
 * - 右侧: ResumePreview (简历预览)
 * 
 * TODO: 后续实现状态管理和API调用
 */

import Sidebar from '../components/Sidebar'
import MatchAnalysis from '../components/MatchAnalysis'
import ResumePreview from '../components/ResumePreview'

function MatchAnalysisPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* 左侧边栏 */}
      <Sidebar />

      {/* 中间分析区域 */}
      <MatchAnalysis />

      {/* 右侧预览区域 */}
      <ResumePreview />
    </div>
  )
}

export default MatchAnalysisPage
