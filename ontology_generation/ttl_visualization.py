import rdflib
import networkx as nx
from pyvis.network import Network
from rdflib.namespace import RDF, RDFS
from pathlib import Path
import math
import json
import webbrowser
from typing import Dict, Set, Tuple, List, Optional


class KnowledgeGraphVisualizer:
    """优化后的紧凑大字体中文知识图谱可视化器"""

    # 节点样式配置（增大字号并优化颜色）
    NODE_STYLES = {
        # 第一组：AI concepts，AI概念
        "AISystem": {
            "zh": {"shape": "image", "chinese": "AI系统", "size": 40,
                  "image": 'https://bkimg.cdn.bcebos.com/pic/fcfaaf51f3deb48f8c543bd53a542d292df5e0fed22e'},
            "en": {"shape": "image", "english": "AI System", "size": 40,
                  "image": 'https://bkimg.cdn.bcebos.com/pic/fcfaaf51f3deb48f8c543bd53a542d292df5e0fed22e'}
        },
        "AICapability": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "AI能力"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "AI Capability"}
        },
        "Modality": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "模态"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "Modality"}
        },
        "AILifecyclePhase": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "AI生命周期阶段"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "AI Lifecycle Phase"}
        },
        "AIComponent": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "AI组件"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "AI Component"}
        },
        "AIModel": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "AI模型"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "AI Model"}
        },
        "GPAIModel": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "通用AI模型"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "General Purpose AI Model"}
        },
        "Data": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "数据"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "Data"}
        },
        "HardwarePlatform": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "硬件平台"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "Hardware Platform"}
        },
        "Input": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "输入"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "Input"}
        },
        "Output": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "输出"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "Output"}
        },
        "AIQuality": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "AI质量"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "AI Quality"}
        },
        "Version": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "版本"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "Version"}
        },
        "License": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "许可证"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "License"}
        },
        "LegalPrecedent": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "法律先例"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "Legal Precedent"}
        },

        # 第二组：AI use concepts，AI使用概念
        "Purpose": {
            "zh": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "chinese": "目的"},
            "en": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "english": "Purpose"}
        },
        "LocalityOfUse": {
            "zh": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "chinese": "使用地点"},
            "en": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "english": "Locality of Use"}
        },
        "ModeOfOutputControllability": {
            "zh": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "chinese": "输出可控性模式"},
            "en": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "english": "Mode of Output Controllability"}
        },
        "AutomationLevel": {
            "zh": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "chinese": "自动化水平"},
            "en": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "english": "Automation Level"}
        },
        "HumanInvolvement": {
            "zh": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "chinese": "人类参与"},
            "en": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "english": "Human Involvement"}
        },
        "Domain": {
            "zh": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "chinese": "领域"},
            "en": {"color": "#A9DADC", "shape": "dot", "size": 25, "font": 22, "english": "Domain"}
        },

        # 第三组：Risk concepts，风险概念
        "Risk": {
            "zh": {"shape": "image", "chinese": "风险", "size": 40,
                  "image": 'https://img1.baidu.com/it/u=3291325220,2145207719&fm=253&fmt=auto&app=120&f=JPEG?w=500&h=500'},
            "en": {"shape": "image", "english": "Risk", "size": 40,
                  "image": 'https://img1.baidu.com/it/u=3291325220,2145207719&fm=253&fmt=auto&app=120&f=JPEG?w=500&h=500'}
        },
        "RiskConcept": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "风险概念"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Risk Source"}
        },
        "RiskSource": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "风险来源"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Risk Source"}
        },
        "Hazard": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "危害"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Hazard"}
        },
        "Threat": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "威胁"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Threat"}
        },
        "Misuse": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "误用"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Misuse"}
        },
        "Vulnerability": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "漏洞"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Vulnerability"}
        },
        "RiskControl": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "风险控制"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Risk Control"}
        },
        "Likelihood": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "可能性"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Likelihood"}
        },
        "Consequence": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "后果"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Consequence"}
        },
        "Controversy": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "争议"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Controversy"}
        },
        "Impact": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "影响"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Impact"}
        },
        "AreaOfImpact": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "影响区域"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Area of Impact"}
        },
        "AITechnique": {
            "zh": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "chinese": "AI技术"},
            "en": {"color": "#8996F4", "shape": "dot", "size": 25, "font": 22, "english": "AI Technique"}
        },
        "Severity": {
            "zh": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "chinese": "严重性"},
            "en": {"color": "#EDC26C", "shape": "dot", "size": 25, "font": 22, "english": "Severity"}
        },

        # 第四组：Stakeholder concepts，利益相关者概念
        "Stakeholder": {
            "zh": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "chinese": "利益相关者"},
            "en": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "english": "Stakeholder"}
        },
        "AIOperator": {
            "zh": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "chinese": "AI操作员"},
            "en": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "english": "AI Operator"}
        },
        "AIProvider": {
            "zh": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "chinese": "AI提供者"},
            "en": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "english": "AI Provider"}
        },
        "AIDeployer": {
            "zh": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "chinese": "AI部署者"},
            "en": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "english": "AI Deployer"}
        },
        "AIDeveloper": {
            "zh": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "chinese": "AI开发者"},
            "en": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "english": "AI Developer"}
        },
        "AIUser": {
            "zh": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "chinese": "AI用户"},
            "en": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "english": "AI User"}
        },
        "AISubject": {
            "zh": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "chinese": "AI主体"},
            "en": {"color": "#4CAC8C", "shape": "dot", "size": 25, "font": 22, "english": "AI Subject"}
        },

        # 第五组：other concepts，其他概念  
        "default": {
            "zh": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "chinese": "默认"},
            "en": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "english": "Default"}
        },
        "Frequency": {
            "zh": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "chinese": "频率"},
            "en": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "english": "Frequency"}
        },
        "Documentation": {
            "zh": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "chinese": "文件"},
            "en": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "english": "Documentation"}
        },
        "Standard": {
            "zh": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "chinese": "标准"},
            "en": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "english": "Standard"}
        },
        "Regulation": {
            "zh": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "chinese": "规定"},
            "en": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "english": "Regulation"}
        },
        "CodeOfConduct": {
            "zh": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "chinese": "行为准则"},
            "en": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "english": "Code Of Conduct"}
        },
        "Change": {
            "zh": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "chinese": "改变"},
            "en": {"color": "#E8EEF2", "shape": "dot", "size": 25, "font": 22, "english": "Change"}
        }
    }

    # 完整中文边标签映射（新增智能补全机制）
    EDGE_LABELS = {
        "zh": {
            "https://w3id.org/airo#compliesWithRegulation": "遵守法规",
            "https://w3id.org/airo#conformsToStandard": "符合标准",
            "https://w3id.org/airo#detectsRiskConcept": "检测风险概念",
            "https://w3id.org/airo#eliminatesRiskConcept": "消除风险概念",
            "https://w3id.org/airo#exploitsVulnerability": "利用漏洞",
            "https://w3id.org/airo#followsCodeOfConduct": "遵循行为准则",
            "https://w3id.org/airo#hasAISubject": "有AI主体",
            "https://w3id.org/airo#hasAIUser": "有AI用户",
            "https://w3id.org/airo#hasAutomationLevel": "有自动化水平",
            "https://w3id.org/airo#hasCapability": "有能力",
            "https://w3id.org/airo#hasChangedEntity": "有改变的实体",
            "https://w3id.org/airo#hasComponent": "有组件",
            "https://w3id.org/airo#hasConsequence": "有后果",
            "https://w3id.org/airo#hasControlOverAIOutput": "控制AI输出",
            "https://w3id.org/airo#hasDocumentation": "有文档",
            "https://w3id.org/airo#hasFrequency": "有频率",
            "https://w3id.org/airo#hasHumanInvolvement": "有人类参与",
            "https://w3id.org/airo#hasImpact": "有影响",
            "https://w3id.org/airo#hasImpactOnArea": "对领域有影响",
            "https://w3id.org/airo#hasImpactOnEntity": "对实体有影响",
            "https://w3id.org/airo#hasImpactOnStakeholder": "对利益相关者有影响",
            "https://w3id.org/airo#hasInput": "有输入",
            "https://w3id.org/airo#hasLicense": "有许可证",
            "https://w3id.org/airo#hasLifecyclePhase": "有生命周期阶段",
            "https://w3id.org/airo#hasLikelihood": "有可能性",
            "https://w3id.org/airo#hasModality": "有模式",
            "https://w3id.org/airo#hasModel": "有模型",
            "https://w3id.org/airo#hasPreDeterminedChange": "有预定的变化",
            "https://w3id.org/airo#hasPurpose": "有目的",
            "https://w3id.org/airo#hasResidualRisk": "有残余风险",
            "https://w3id.org/airo#hasRisk": "有风险",
            "https://w3id.org/airo#hasRiskControl": "有风险控制",
            "https://w3id.org/airo#hasRiskSource": "有风险来源",
            "https://w3id.org/airo#hasSeverity": "有严重性",
            "https://w3id.org/airo#hasStakeholder": "有利益相关者",
            "https://w3id.org/airo#hasTestingData": "有测试数据",
            "https://w3id.org/airo#hasTrainingData": "有训练数据",
            "https://w3id.org/airo#hasValidationData": "有验证数据",
            "https://w3id.org/airo#hasVersion": "有版本",
            "https://w3id.org/airo#hasVulnerability": "有漏洞",
            "https://w3id.org/airo#isAppliedWithinDomain": "在领域内应用",
            "https://w3id.org/airo#isDeployedBy": "由...部署",
            "https://w3id.org/airo#isDevelopedBy": "由...开发",
            "https://w3id.org/airo#isFollowedByControl": "后接控制",
            "https://w3id.org/airo#isPartOfControl": "是控制的一部分",
            "https://w3id.org/airo#isProvidedBy": "由...提供",
            "https://w3id.org/airo#isRiskSourceFor": "是...的风险来源",
            "https://w3id.org/airo#isUsedWithinLocality": "在地方使用",
            "https://w3id.org/airo#mitigatesRiskConcept": "缓解风险概念",
            "https://w3id.org/airo#modifiesRiskConcept": "修改风险概念",
            "https://w3id.org/airo#producesOutput": "产生输出",
            "https://w3id.org/airo#runsOnHardware": "运行在硬件上",
            "https://w3id.org/airo#usesTechnique": "使用技术",
            "https://w3id.org/dpv#hasData": "有数据",
            "https://w3id.org/dpv#hasDataSource": "有数据源",
            "https://w3id.org/dpv#hasDataSubject": "有数据主体",
            "https://w3id.org/dpv#hasLegalBasis": "有法律依据",
            "https://w3id.org/dpv#hasProcessing": "有处理"
        },
        "en": {
            "https://w3id.org/airo#compliesWithRegulation": "Complies with Regulation",
            "https://w3id.org/airo#conformsToStandard": "Conforms to Standard",
            "https://w3id.org/airo#detectsRiskConcept": "Detects Risk Concept",
            "https://w3id.org/airo#eliminatesRiskConcept": "Eliminates Risk Concept",
            "https://w3id.org/airo#exploitsVulnerability": "Exploits Vulnerability",
            "https://w3id.org/airo#followsCodeOfConduct": "Follows Code of Conduct",
            "https://w3id.org/airo#hasAISubject": "Has AI Subject",
            "https://w3id.org/airo#hasAIUser": "Has AI User",
            "https://w3id.org/airo#hasAutomationLevel": "Has Automation Level",
            "https://w3id.org/airo#hasCapability": "Has Capability",
            "https://w3id.org/airo#hasChangedEntity": "Has Changed Entity",
            "https://w3id.org/airo#hasComponent": "Has Component",
            "https://w3id.org/airo#hasConsequence": "Has Consequence",
            "https://w3id.org/airo#hasControlOverAIOutput": "Has Control Over AI Output",
            "https://w3id.org/airo#hasDocumentation": "Has Documentation",
            "https://w3id.org/airo#hasFrequency": "Has Frequency",
            "https://w3id.org/airo#hasHumanInvolvement": "Has Human Involvement",
            "https://w3id.org/airo#hasImpact": "Has Impact",
            "https://w3id.org/airo#hasImpactOnArea": "Has Impact On Area",
            "https://w3id.org/airo#hasImpactOnEntity": "Has Impact On Entity",
            "https://w3id.org/airo#hasImpactOnStakeholder": "Has Impact On Stakeholder",
            "https://w3id.org/airo#hasInput": "Has Input",
            "https://w3id.org/airo#hasLicense": "Has License",
            "https://w3id.org/airo#hasLifecyclePhase": "Has Lifecycle Phase",
            "https://w3id.org/airo#hasLikelihood": "Has Likelihood",
            "https://w3id.org/airo#hasModality": "Has Modality",
            "https://w3id.org/airo#hasModel": "Has Model",
            "https://w3id.org/airo#hasPreDeterminedChange": "Has Pre-determined Change",
            "https://w3id.org/airo#hasPurpose": "Has Purpose",
            "https://w3id.org/airo#hasResidualRisk": "Has Residual Risk",
            "https://w3id.org/airo#hasRisk": "Has Risk",
            "https://w3id.org/airo#hasRiskControl": "Has Risk Control",
            "https://w3id.org/airo#hasRiskSource": "Has Risk Source",
            "https://w3id.org/airo#hasSeverity": "Has Severity",
            "https://w3id.org/airo#hasStakeholder": "Has Stakeholder",
            "https://w3id.org/airo#hasTestingData": "Has Testing Data",
            "https://w3id.org/airo#hasTrainingData": "Has Training Data",
            "https://w3id.org/airo#hasValidationData": "Has Validation Data",
            "https://w3id.org/airo#hasVersion": "Has Version",
            "https://w3id.org/airo#hasVulnerability": "Has Vulnerability",
            "https://w3id.org/airo#isAppliedWithinDomain": "Is Applied Within Domain",
            "https://w3id.org/airo#isDeployedBy": "Is Deployed By",
            "https://w3id.org/airo#isDevelopedBy": "Is Developed By",
            "https://w3id.org/airo#isFollowedByControl": "Is Followed By Control",
            "https://w3id.org/airo#isPartOfControl": "Is Part Of Control",
            "https://w3id.org/airo#isProvidedBy": "Is Provided By",
            "https://w3id.org/airo#isRiskSourceFor": "Is Risk Source For",
            "https://w3id.org/airo#isUsedWithinLocality": "Is Used Within Locality",
            "https://w3id.org/airo#mitigatesRiskConcept": "Mitigates Risk Concept",
            "https://w3id.org/airo#modifiesRiskConcept": "Modifies Risk Concept",
            "https://w3id.org/airo#producesOutput": "Produces Output",
            "https://w3id.org/airo#runsOnHardware": "Runs On Hardware",
            "https://w3id.org/airo#usesTechnique": "Uses Technique",
            "https://w3id.org/dpv#hasData": "Has Data",
            "https://w3id.org/dpv#hasDataSource": "Has Data Source",
            "https://w3id.org/dpv#hasDataSubject": "Has Data Subject",
            "https://w3id.org/dpv#hasLegalBasis": "Has Legal Basis",
            "https://w3id.org/dpv#hasProcessing": "Has Processing"
        }
    }

    def __init__(self, physics_enabled: bool = True, language: str = "zh"):
        self.physics_enabled = physics_enabled
        self.language = language
        self._init_adaptive_layout()

    def _init_adaptive_layout(self):
        """自适应布局参数"""
        self.layout_factor = 0.8  # 紧凑系数 (0.5-1.0)
        self.left_center = (-600 * self.layout_factor, 0)
        self.right_center = (600 * self.layout_factor, 0)
        self.cluster_radius = 600 * self.layout_factor
        # 增加边的长度，通过增大 spring_length 实现
        self.spring_length = 300 * self.layout_factor
        self.node_spacing = 120 * self.layout_factor

    def load_graph(self, file_path: Path) -> rdflib.Graph:
        """加载并解析RDF图"""
        g = rdflib.Graph()
        try:
            g.parse(file_path, format="turtle")
            # print(f"成功加载RDF图，包含 {len(g)} 个三元组")
            return g
        except Exception as e:
            raise RuntimeError(f"RDF文件解析失败: {str(e)}")

    # def _extract_labels(self, g: rdflib.Graph) -> Dict[str, str]:
    #     """提取节点标签"""
    #     labels = {}
    #     for s in g.subjects(RDF.type, None):
    #         if (s, RDFS.label, None) in g:
    #             # 根据当前语言设置提取标签
    #             label = g.value(s, RDFS.label, default=None, any=False, lang=self.language)
    #             if label is not None:
    #                 labels[str(s)] = str(label)
    #             else:
    #                 # 如果没有找到指定语言的标签，则使用默认标签
    #                 labels[str(s)] = str(g.value(s, RDFS.label))
    #     return labels

    def _extract_labels(self, g: rdflib.Graph) -> Dict[str, str]:
        """提取节点标签"""
        labels = {}
        for s in g.subjects(RDF.type, None):
            if (s, RDFS.label, None) in g:
                # 获取所有标签
                all_labels = list(g.objects(s, RDFS.label))
                # 根据当前语言设置提取标签
                label = next((str(l) for l in all_labels if l.language == self.language), None)
                if label is not None:
                    labels[str(s)] = label
                else:
                    # 如果没有找到指定语言的标签，则使用默认标签
                    labels[str(s)] = str(next(iter(all_labels), ''))
        return labels

    def _get_short_uri(self, uri: str) -> str:
        """智能URI缩写"""
        parts = uri.split("#")[-1].split("/")[-1].split("_")
        return " ".join(part.capitalize() for part in parts[-2:])

    def process_graph(self, g: rdflib.Graph) -> Tuple[Set[str], Dict[str, dict]]:
        """处理图谱数据"""
        entities = set()
        node_data = {}
        labels = self._extract_labels(g)

        # 定义AIRO命名空间
        AIRO = rdflib.Namespace("https://w3id.org/airo#")

        # 自动补全缺失的边标签
        existing_predicates = set(self.EDGE_LABELS[self.language].keys())
        graph_predicates = {str(p) for s, p, o in g}
        for p in graph_predicates - existing_predicates:
            self.EDGE_LABELS[self.language][p] = self._get_short_uri(p)

        # 第一遍：收集所有类型信息
        type_mapping = {}
        for s, p, o in g:
            if p == RDF.type:
                uri = str(s)
                type_uri = str(o)
                # 精确匹配AIRO中的类型
                if type_uri.startswith("https://w3id.org/airo#"):
                    short_type = type_uri.split("#")[-1]
                    if short_type in self.NODE_STYLES:  # 只保留我们定义的类型
                        type_mapping[uri] = short_type
                else:
                    # 处理其他命名空间的类型
                    type_mapping[uri] = self._get_short_uri(type_uri)

        # 第二遍：构建节点数据
        for s, p, o in g:
            if isinstance(s, rdflib.URIRef):
                uri = str(s)
                if uri not in node_data:
                    node_data[uri] = {
                        'uri': uri,
                        'label': labels.get(uri, self._get_short_uri(uri)),
                        'type': type_mapping.get(uri, None),
                        'properties': []
                    }

                if p != RDF.type:  # 类型信息已经处理过
                    node_data[uri]['properties'].append((
                        self._get_short_uri(str(p)),
                        self._get_short_uri(str(o)) if isinstance(o, rdflib.URIRef) else str(o)
                    ))
                entities.add(uri)

            if isinstance(o, rdflib.URIRef):
                uri = str(o)
                if uri not in node_data:
                    node_data[uri] = {
                        'uri': uri,
                        'label': labels.get(uri, self._get_short_uri(uri)),
                        'type': type_mapping.get(uri, None),
                        'properties': []
                    }
                entities.add(uri)

        # print("Entities:", entities)
        # print("Node Data:", node_data)
        return entities, node_data

    def create_network(self, g: rdflib.Graph, entities: Set[str], node_data: Dict[str, dict]) -> nx.DiGraph:
        """创建网络图结构"""
        G = nx.DiGraph()
        existing_node_types = set()  # 新增：用于存储实际存在的节点类型

        # 添加节点
        for node in entities:
            data = node_data.get(node, {'uri': node, 'label': self._get_short_uri(node)})
            G.add_node(node, **data)
            node_type = data.get('type', 'default')
            existing_node_types.add(node_type)  # 记录节点类型

        # 添加边
        for s, p, o in g:
            if p == RDF.type:
                continue
            if str(o) in entities and isinstance(s, rdflib.URIRef):
                pred = str(p)
                label = self.EDGE_LABELS[self.language].get(pred, self._get_short_uri(pred))
                G.add_edge(str(s), str(o),
                           label=label,
                           original_pred=pred,
                           font={'size': 20})

        # 删除孤立节点
        isolated_nodes = list(nx.isolates(G))
        for node in isolated_nodes:
            G.remove_node(node)

        # print(f"图谱统计 - 节点: {G.number_of_nodes()}, 边: {G.number_of_edges()}")
        return G, existing_node_types  # 返回实际存在的节点类型

    def _partition_nodes(self, G: nx.DiGraph, nodes: List[str],
                         left_anchors: List[str], right_anchors: List[str]) -> Tuple[List[str], List[str]]:
        """智能节点分区算法"""
        if not left_anchors or not right_anchors:
            return (nodes[:len(nodes) // 2], nodes[len(nodes) // 2:])

        left_group = []
        right_group = []
        for n in nodes:
            left_score = sum(1 for a in left_anchors if nx.has_path(G, n, a))
            right_score = sum(1 for a in right_anchors if nx.has_path(G, n, a))

            if left_score > right_score:
                left_group.append(n)
            elif right_score > left_score:
                right_group.append(n)
            else:
                # 平衡分配
                if len(left_group) <= len(right_group):
                    left_group.append(n)
                else:
                    right_group.append(n)

        return left_group, right_group

    def visualize(self, G: nx.DiGraph, node_data: Dict[str, dict], output_path: Path, existing_node_types: Set[str]):
        """执行可视化"""
        net = Network(
            directed=True,
            height="100vh",
            width="100%",
            bgcolor="#ffffff",
            font_color="#2c3e50",
            notebook=False
        )

        # 识别核心节点
        ai_systems = [n for n, d in G.nodes(data=True) if d.get('type') == 'AISystem']
        risks = [n for n, d in G.nodes(data=True) if d.get('type') == 'Risk']

        # 核心节点布局
        self._arrange_core_nodes(net, ai_systems, node_data, self.left_center)
        self._arrange_core_nodes(net, risks, node_data, self.right_center)

        # 其他节点智能分区
        other_nodes = [n for n in G.nodes() if n not in ai_systems + risks]
        left_nodes, right_nodes = self._partition_nodes(G, other_nodes, ai_systems, risks)

        # 集群布局
        self._arrange_cluster(net, left_nodes, node_data, self.left_center)
        self._arrange_cluster(net, right_nodes, node_data, self.right_center)

        # 添加边
        self._add_edges(net, G)

        # 配置物理引擎
        self._configure_physics(net)

        # 保存并优化显示
        self._save_visualization(net, output_path, existing_node_types)

        # 自动打开预览
        webbrowser.open(str(output_path))

    def _arrange_core_nodes(self, net: Network, nodes: List[str],
                            node_data: Dict[str, dict], center: Tuple[float, float]):
        """核心节点布局"""
        for i, node in enumerate(nodes):
            data = node_data[node]
            node_type = data.get('type', 'default')
            # print(f"Node: {node}, Type: {node_type}")
            style = self.NODE_STYLES[node_type][self.language]
            label = f"{style.get('chinese' if self.language == 'zh' else 'english', '')}：\n{data['label']}"
            
            # 根据节点类型调整布局
            if node_type == 'Risk':
                # 对于Risk节点，使用更大的半径和更均匀的分布
                radius = 100  # 增加半径
                angle = 2 * math.pi * i / len(nodes)
                x = center[0] + radius * math.cos(angle)
                y = center[1] + radius * math.sin(angle)
            else:
                # 对于其他节点，使用较小的半径
                angle = 2 * math.pi * i / len(nodes)
                x = center[0] + 10 * math.cos(angle)
                y = center[1] + 10 * math.sin(angle)

            # 节点选项
            node_options = {
                'x': x,
                'y': y,
                'fixed': node_type != 'Risk',  # 只有Risk节点不固定
                'physics': node_type != 'Risk',  # 只有Risk节点启用物理引擎
                'label': label,
                'size': style["size"],
                'title': self._generate_tooltip(data)
            }

            # 如果样式中有image属性，则使用image
            if 'image' in style:
                node_options.update({
                    'shape': 'image',
                    'image': style['image']
                })
            # 否则使用shape
            else:
                node_options['shape'] = style['shape']

            net.add_node(node, **node_options)

    def _arrange_cluster(self, net: Network, nodes: List[str],
                         node_data: Dict[str, dict], center: Tuple[float, float]):
        """集群节点布局"""
        angle_step = 2 * math.pi / max(len(nodes), 1)
        for i, node in enumerate(nodes):
            distance = self.cluster_radius * (0.4 + 0.2 * (i % 4))
            angle = angle_step * i
            x = center[0] + distance * math.cos(angle)
            y = center[1] + distance * math.sin(angle)

            data = node_data[node]
            node_type = data.get('type', 'default')
            # print(f"Node: {node}, Type: {node_type}")
            style = self.NODE_STYLES.get(node_type, self.NODE_STYLES["default"])[self.language]

            # 修改标签以包含节点类型
            label = f"{style.get('chinese' if self.language == 'zh' else 'english', '')}：\n{data['label']}"

            net.add_node(
                node,
                label=label,
                title=self._generate_tooltip(data),
                color=style["color"],
                shape=style["shape"],
                size=style["size"],
                font={"size": 20, "face": "Microsoft YaHei" if self.language == "zh" else "Arial"},
                x=x,
                y=y,
                fixed=False,
                physics=self.physics_enabled
            )

    def _add_edges(self, net: Network, G: nx.DiGraph):
        """添加带中文标签的边"""
        for u, v, data in G.edges(data=True):
            net.add_edge(
                u, v,
                label=data["label"],
                width=3,
                # color="rgba(100,100,100,0.7)",
                color="rgb(197, 191, 173)",
                arrows={"to": {"enabled": True, "scaleFactor": 1.2}},
                font={"size": 14, "face": "Microsoft YaHei"},
                smooth={"type": "dynamic", "roundness": 0.4},
                physics=True
            )

    def _configure_physics(self, net: Network):
        """配置物理引擎参数"""
        physics_config = {
            "physics": {
                "enabled": self.physics_enabled,
                "solver": "barnesHut",
                "barnesHut": {
                    "gravitationalConstant": -8000 * self.layout_factor,
                    "centralGravity": 0.3,
                    "springLength": self.spring_length,
                    "springConstant": 0.08,
                    "damping": 0.2,
                    "avoidOverlap": 0.5
                },
                "minVelocity": 1.0,
                "maxVelocity": 50,
                "stabilization": {
                    "enabled": True,
                    "iterations": 500,
                    "updateInterval": 25
                }
            }
        }
        # print("Physics Config:", physics_config)
        net.set_options(json.dumps(physics_config))

    def _generate_tooltip(self, data: dict) -> str:
        """生成HTML工具提示"""
        tooltip = f"""
        <div style="
            font-family: Microsoft YaHei, sans-serif;
            font-size: 16px;
            max-width: 300px;
            padding: 10px;
            border-radius: 5px;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1)">
            <div style="
                color: {data.get('color', '#2c3e50')};
                font-weight: bold;
                margin-bottom: 8px;
                border-bottom: 2px solid #eee;
                padding-bottom: 5px">
                <div style="font-weight: bold; font-size: 16px;">{data.get('type', '未分类')}</div>
                {data['label']}
            </div>
            <div style="margin-bottom: 5px">
                <span style="color: #666">类型：</span>
                {data.get('type', '未分类')}
            </div>
            {self._format_properties(data.get('properties', []))}
        </div>
        """
        return tooltip

    def _format_properties(self, properties: List[tuple]) -> str:
        """格式化属性列表"""
        if not properties:
            return ""
        items = "\n".join(
            f'<div style="margin: 3px 0; color: #444">'
            f'<span style="color: #888">{prop}:</span> {value}'
            f'</div>'
            for prop, value in properties[:5]  # 显示前5个属性
        )
        return f"""
        <div style="
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #eee">
            {items}
        </div>
        """

    def _save_visualization(self, net: Network, output_path: Path, existing_node_types: Set[str]):
        """保存并增强可视化效果"""
        net.save_graph(str(output_path))

        # 生成图例 HTML
        legend_html = '<div id="legend" style="position: absolute; top: 20px; right: 20px; background-color: white; padding: 10px; border: 1px solid #ccc; border-radius: 5px; z-index: 100;">'
        legend_html += f'<h3 style="margin-bottom: 10px; font-family: {"Microsoft YaHei" if self.language == "zh" else "Arial"};">{"图例说明" if self.language == "zh" else "Legend"}</h3>'

        # 分组标题
        group_titles = {
            "zh": {
                "AI concepts": "AI概念",
                "AI use concepts": "AI使用概念",
                "Risk concepts": "风险概念",
                "Stakeholder concepts": "利益相关者概念",
                "other concepts": "其他概念"
            },
            "en": {
                "AI concepts": "AI Concepts",
                "AI use concepts": "AI Use Concepts",
                "Risk concepts": "Risk Concepts",
                "Stakeholder concepts": "Stakeholder Concepts",
                "other concepts": "Other Concepts"
            }
        }

        # 分组节点
        group_nodes = {
            "AI concepts": ["AISystem", "AICapability", "Modality", "AILifecyclePhase", "AIComponent", "AIModel", "GPAIModel", "Data", "HardwarePlatform", "Input", "Output", "AIQuality", "Version", "License", "LegalPrecedent", "AITechnique"],
            "AI use concepts": ["Purpose", "LocalityOfUse", "ModeOfOutputControllability", "AutomationLevel", "HumanInvolvement", "Domain"],
            "Risk concepts": ["Risk", "RiskSource", "Hazard", "Threat", "Misuse", "Vulnerability", "RiskControl", "Likelihood", "Consequence", "Controversy", "Impact", "AreaOfImpact", "Severity"],
            "Stakeholder concepts": ["Stakeholder", "AIOperator", "AIProvider", "AIDeployer", "AIDeveloper", "AIUser", "AISubject"],
            "other concepts": ["default"]
        }

        # 生成分组图例
        for group, nodes in group_nodes.items():
            if any(node in existing_node_types for node in nodes):  # 仅显示实际存在的节点类型
                legend_html += f'<div style="font-weight: bold; font-family: {"Microsoft YaHei" if self.language == "zh" else "Arial"}; margin-top: 10px;">{group_titles[self.language][group]}</div>'
                for node_type in nodes:
                    if node_type in existing_node_types:
                        style = self.NODE_STYLES[node_type][self.language]
                        legend_html += f'<div style="display: flex; align-items: center; margin-bottom: 5px;">'
                        
                        # 处理图例显示
                        if 'image' in style:
                            # 如果是图片节点，显示图片
                            legend_html += f'<img src="{style["image"]}" style="width: 20px; height: 20px; margin-right: 10px;">'
                        else:
                            # 如果是普通节点，显示形状和颜色
                            legend_html += f'<div style="width: 20px; height: 20px; margin-right: 10px; '
                            if 'color' in style:
                                legend_html += f'background-color: {style["color"]}; '
                            if style.get('shape') == 'diamond':
                                legend_html += 'transform: rotate(45deg);'
                            legend_html += f'"></div>'
                        
                        legend_html += f'<span style="font-family: {"Microsoft YaHei" if self.language == "zh" else "Arial"};">{style.get("chinese" if self.language == "zh" else "english", node_type)}</span>'
                        legend_html += '</div>'
        legend_html += '</div>'

        # 注入自定义样式和字体以及图例
        custom_styles = f"""
        <style>
            @font-face {{
                font-family: 'Microsoft YaHei';
                src: url('https://cdn.jsdelivr.net/npm/@fontsource/microsoft-yahei@4.5.0/files/microsoft-yahei-chinese-simplified-400-normal.woff2') format('woff2');
            }}
            body {{
                margin: 0;
                overflow: hidden;
                font-family: {"Microsoft YaHei" if self.language == "zh" else "Arial"}, "PingFang SC", sans-serif;
            }}
            #mynetwork {{
                background: #f8f9fa;
            }}
            .vis-tooltip {{
                font-family: {"Microsoft YaHei" if self.language == "zh" else "Arial"} !important;
                font-size: 16px !important;
                max-width: 320px !important;
                border-radius: 6px !important;
                pointer-events: none;
            }}
        </style>
        """

        with open(output_path, "r+", encoding="utf-8") as f:
            content = f.read()
            content = content.replace("</body>", f"{legend_html}</body>")
            content = content.replace("</head>", f"{custom_styles}</head>")
            f.seek(0)
            f.write(content)
            f.truncate()


def visualize_ttl_file(ttl_file_path: str):
    """可视化给定路径的TTL文件"""
    try:
        # 生成中文版本
        visualizer_zh = KnowledgeGraphVisualizer(physics_enabled=True, language="zh")
        input_file = Path(ttl_file_path)
        output_file_zh = input_file.parent / f"{input_file.stem}_zh.html"

        # print("正在加载和处理中文图谱数据...")
        g = visualizer_zh.load_graph(input_file)
        entities, node_data = visualizer_zh.process_graph(g)
        G, existing_node_types = visualizer_zh.create_network(g, entities, node_data)
        #
        print("生成中文优化可视化...")
        visualizer_zh.visualize(G, node_data, output_file_zh, existing_node_types)

        # 生成英文版本
        visualizer_en = KnowledgeGraphVisualizer(physics_enabled=True, language="en")
        output_file_en = input_file.parent / f"{input_file.stem}_en.html"

        # print("正在加载和处理英文图谱数据...")
        g = visualizer_en.load_graph(input_file)
        entities, node_data = visualizer_en.process_graph(g)
        G, existing_node_types = visualizer_en.create_network(g, entities, node_data)

        # print("生成英文优化可视化...")
        visualizer_en.visualize(G, node_data, output_file_en, existing_node_types)

        print(f"中文可视化已保存至：{output_file_zh}")
        print(f"英文可视化已保存至：{output_file_en}")
        
        # # 自动打开预览
        # webbrowser.open(str(output_file_zh))
        # webbrowser.open(str(output_file_en))
    except Exception as e:
        print(f"处理过程中发生错误：{str(e)}")
        raise


if __name__ == "__main__":
    visualize_ttl_file("incidentinfo/ontology_incident_2285.ttl")
