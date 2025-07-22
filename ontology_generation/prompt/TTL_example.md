# TTL-example

## 1. AI Attack

@prefix airo: <https://w3id.org/airo#> .
@prefix : <https://w3id.org/airo#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix terms: <http://purl.org/dc/terms/> .
@base <https://w3id.org/airo#> .

:AIAttackOnHarbinAsianWinterGames rdf:type airo:AISystem ;
    rdfs:label "AI Attack on Harbin Asian Winter Games"@en ;
    rdfs:label "AI攻击哈尔滨亚冬会"@zh ;
    airo:hasRisk :CyberAttackRisk ;
    airo:isDevelopedBy :USNationalSecurityAgency ;
    airo:hasStakeholder :ChinaNationalComputerVirusEmergencyResponseCenter , :360Group ;
    airo:hasImpactOnEntity :CriticalInformationInfrastructure , :SportsEventInformationSystem ;
    airo:usesTechnique :AITechniquesForAttack .

:CyberAttackRisk rdf:type airo:Risk ;
    rdfs:label "Cyber Attack Risk"@en ;
    rdfs:label "网络攻击风险"@zh ;
    airo:hasConsequence :DataTheft , :ServiceDisruption .

:DataTheft rdf:type airo:Consequence ;
    rdfs:label "Data Theft"@en ;
    rdfs:label "数据盗窃"@zh ;
    airo:hasImpact :PrivacyViolation , :EconomicLoss .

:ServiceDisruption rdf:type airo:Consequence ;
    rdfs:label "Service Disruption"@en ;
    rdfs:label "服务中断"@zh ;
    airo:hasImpact :OperationalDisruption , :PublicSafetyThreat .

:PrivacyViolation rdf:type airo:Impact ;
    rdfs:label "Privacy Violation"@en ;
    rdfs:label "隐私侵犯"@zh .

:EconomicLoss rdf:type airo:Impact ;
    rdfs:label "Economic Loss"@en ;
    rdfs:label "经济损失"@zh .

:OperationalDisruption rdf:type airo:Impact ;
    rdfs:label "Operational Disruption"@en ;
    rdfs:label "运营中断"@zh .

:PublicSafetyThreat rdf:type airo:Impact ;
    rdfs:label "Public Safety Threat"@en ;
    rdfs:label "公共安全威胁"@zh .

:USNationalSecurityAgency rdf:type airo:AIDeveloper ;
    rdfs:label "US National Security Agency"@en ;
    rdfs:label "美国国家安全局"@zh .

:ChinaNationalComputerVirusEmergencyResponseCenter rdf:type airo:Stakeholder ;
    rdfs:label "China National Computer Virus Emergency Response Center"@en ;
    rdfs:label "中国国家计算机病毒应急处理中心"@zh .

:360Group rdf:type airo:Stakeholder ;
    rdfs:label "360 Group"@en ;
    rdfs:label "360集团"@zh .

:CriticalInformationInfrastructure rdf:type airo:AreaOfImpact ;
    rdfs:label "Critical Information Infrastructure"@en ;
    rdfs:label "关键信息基础设施"@zh .

:SportsEventInformationSystem rdf:type airo:AreaOfImpact ;
    rdfs:label "Sports Event Information System"@en ;
    rdfs:label "体育赛事信息系统"@zh .

:AITechniquesForAttack rdf:type airo:AITechnique ;
    rdfs:label "AI Techniques for Attack"@en ;
    rdfs:label "用于攻击的人工智能技术"@zh .

## 2. Uber autonomous vehicle

@prefix airo: <https://w3id.org/airo#> .
@prefix : <https://w3id.org/airo#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix terms: <http://purl.org/dc/terms/> .
@prefix ex: <https://example.com/aievents#> .
@base <https://w3id.org/airo#> .

ex:UberAutonomousVehicle rdf:type airo:AISystem ;
    rdfs:label "Uber Autonomous Vehicle"@en ;
    rdfs:label "优步自动驾驶汽车"@zh ;
    airo:hasRisk ex:PedestrianFatalityRisk ;
    airo:usesTechnique ex:MachineLearning ;
    airo:hasLifecyclePhase ex:TestingPhase ;
    airo:hasImpactOnArea ex:PhysicalSafety ;
    airo:hasSeverity ex:CriticalSeverity .

ex:PedestrianFatalityRisk rdf:type airo:Risk ;
    rdfs:label "Pedestrian Fatality Risk"@en ;
    rdfs:label "行人死亡风险"@zh ;
    airo:isRiskSourceFor ex:SoftwareDefect ;
    airo:isRiskSourceFor ex:DriverDistraction .

ex:SoftwareDefect rdf:type airo:RiskSource ;
    rdfs:label "Software Defect"@en ;
    rdfs:label "软件缺陷"@zh ;
    airo:exploitsVulnerability ex:JaywalkingPedestrianMisclassification .

ex:DriverDistraction rdf:type airo:RiskSource ;
    rdfs:label "Driver Distraction"@en ;
    rdfs:label "驾驶员分心"@zh ;
    airo:exploitsVulnerability ex:HumanMonitoringFailure .

ex:JaywalkingPedestrianMisclassification rdf:type airo:Vulnerability ;
    rdfs:label "Jaywalking Pedestrian Misclassification"@en ;
    rdfs:label "乱穿马路行人误分类漏洞"@zh .

ex:HumanMonitoringFailure rdf:type airo:Vulnerability ;
    rdfs:label "Human Monitoring Failure"@en ;
    rdfs:label "人工监控失效漏洞"@zh .

ex:MachineLearning rdf:type airo:AITechnique ;
    rdfs:label "Machine Learning"@en ;
    rdfs:label "机器学习"@zh .

ex:TestingPhase rdf:type airo:AILifecyclePhase ;
    rdfs:label "Testing Phase"@en ;
    rdfs:label "测试阶段"@zh .

ex:PhysicalSafety rdf:type airo:AreaOfImpact ;
    rdfs:label "Physical Safety"@en ;
    rdfs:label "人身安全"@zh .

ex:CriticalSeverity rdf:type airo:Severity ;
    rdfs:label "Critical Severity"@en ;
    rdfs:label "严重等级：致命"@zh .

## 3. YouTube content

@prefix airo: <https://w3id.org/airo#> .
@prefix : <https://w3id.org/airo#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix terms: <http://purl.org/dc/terms/> .
@prefix ex: <https://example.com/aievents#> .
@base <https://w3id.org/airo#> .

:YouTubeKidsApp rdf:type airo:AISystem ;
    rdfs:label "YouTube Kids App"@en ;
    rdfs:label "YouTube儿童应用"@zh ;
    airo:hasRisk :InappropriateContentRisk ;
    airo:hasCapability :ContentFilteringAlgorithm ;
    airo:isDevelopedBy :Google ;
    airo:hasPurpose :ChildFriendlyVideoPlatform ;
    airo:hasStakeholder :Children .

:InappropriateContentRisk rdf:type airo:Risk ;
    rdfs:label "Inappropriate Content Risk"@en ;
    rdfs:label "不当内容风险"@zh ;
    airo:hasConsequence :ExposureToExplicitMaterial ;
    airo:hasConsequence :PsychologicalDistressForChildren ;
    airo:isRiskSourceFor :PedophiliaJokes ;
    airo:isRiskSourceFor :ViolentCartoons ;
    airo:hasRiskControl :MachineLearningDetectionSystem ;
    airo:hasRiskControl :UserFlaggingMechanism .

:ContentFilteringAlgorithm rdf:type airo:AITechnique ;
    rdfs:label "Content Filtering Algorithm"@en ;
    rdfs:label "内容过滤算法"@zh .

:Google rdf:type airo:AIDeveloper ;
    rdfs:label "Google"@en ;
    rdfs:label "谷歌"@zh .

:ChildFriendlyVideoPlatform rdf:type airo:Purpose ;
    rdfs:label "Child Friendly Video Platform"@en ;
    rdfs:label "儿童友好型视频平台"@zh .

:Children rdf:type airo:AISubject ;
    rdfs:label "Children"@en ;
    rdfs:label "儿童"@zh .

:PedophiliaJokes rdf:type airo:RiskSource ;
    rdfs:label "Pedophilia Jokes"@en ;
    rdfs:label "恋童癖笑话"@zh .

:ViolentCartoons rdf:type airo:RiskSource ;
    rdfs:label "Violent Cartoons"@en ;
    rdfs:label "暴力卡通"@zh .

:ExposureToExplicitMaterial rdf:type airo:Consequence ;
    rdfs:label "Exposure To Explicit Material"@en ;
    rdfs:label "接触不当材料"@zh .

:PsychologicalDistressForChildren rdf:type airo:Impact ;
    rdfs:label "Psychological Distress For Children"@en ;
    rdfs:label "儿童心理困扰"@zh .

:MachineLearningDetectionSystem rdf:type airo:RiskControl ;
    rdfs:label "Machine Learning Detection System"@en ;
    rdfs:label "机器学习检测系统"@zh .

:UserFlaggingMechanism rdf:type airo:RiskControl ;
    rdfs:label "User Flagging Mechanism"@en ;
    rdfs:label "用户举报机制"@zh .