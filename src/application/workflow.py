"""
RAG Workflow - LangGraph

Application Layer: RAG 파이프라인의 흐름을 정의합니다.
각 노드(Domain Layer)를 조합하여 유스케이스를 구성합니다.
"""
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from .state import RAGState
from src.domain.entities import RouteQuery
from src.domain.nodes import QueryRewriteNode, RetrieverNode, GeneratorNode, SimpleGeneratorNode
from src.domain.prompts import ROUTER_SYSTEM_PROMPT
from src.infrastructure import LLMService


class RAGWorkflow:
    """RAG 워크플로우

    LangGraph 기반 상태 머신으로 RAG 파이프라인을 구성합니다.

    흐름:
    1. Router: 질문 분석 → vectorstore or llm
    2-a. RAG 경로: QueryRewrite → Retriever → Generator → END
    2-b. LLM 경로: SimpleGenerator → END

    왜 조건부 라우팅인가?
    - 모든 질문에 RAG를 사용하면 비효율적
    - 인사, 일반 지식 질문은 검색 불필요
    - 라우팅으로 지연시간 & 비용 절감
    """

    def __init__(
        self,
        llm_service: LLMService,
        query_rewrite_node: QueryRewriteNode,
        retriever_node: RetrieverNode,
        generator_node: GeneratorNode,
        simple_generator_node: SimpleGeneratorNode,
    ):
        self._llm_service = llm_service
        self._query_rewrite_node = query_rewrite_node
        self._retriever_node = retriever_node
        self._generator_node = generator_node
        self._simple_generator_node = simple_generator_node
        self._app = None

    def route_question(self, state: RAGState) -> Literal["query_rewrite", "simple_generator"]:
        """질문을 분석하여 경로 결정"""
        print(f"--- [Router] 질문 분석 중: {state['question']} ---")
        llm = self._llm_service.get_rewrite_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", ROUTER_SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        decision = self._llm_service.invoke_with_structured_output(
            llm=llm, prompt=prompt, output_schema=RouteQuery, input_data={"question": state["question"]}
        )
        if decision.datasource == "vectorstore":
            print("--- [Decision] RAG 검색 진행 ---")
            return self._query_rewrite_node.name
        else:
            print("--- [Decision] 일반 대화 진행 ---")
            return self._simple_generator_node.name

    def build(self) -> "RAGWorkflow":
        """워크플로우 빌드"""
        workflow = StateGraph(RAGState)

        # 노드 추가
        workflow.add_node(self._query_rewrite_node.name, self._query_rewrite_node)
        workflow.add_node(self._retriever_node.name, self._retriever_node)
        workflow.add_node(self._generator_node.name, self._generator_node)
        workflow.add_node(self._simple_generator_node.name, self._simple_generator_node)

        # 조건부 진입점 (라우팅)
        workflow.set_conditional_entry_point(
            self.route_question,
            {
                self._query_rewrite_node.name: self._query_rewrite_node.name,
                self._simple_generator_node.name: self._simple_generator_node.name
            }
        )

        # 엣지 정의 (흐름)
        workflow.add_edge(self._query_rewrite_node.name, self._retriever_node.name)
        workflow.add_edge(self._retriever_node.name, self._generator_node.name)
        workflow.add_edge(self._generator_node.name, END)
        workflow.add_edge(self._simple_generator_node.name, END)

        self._app = workflow.compile()
        return self

    @property
    def app(self):
        """컴파일된 워크플로우"""
        if self._app is None:
            raise RuntimeError("Workflow가 빌드되지 않았습니다. build()를 먼저 호출하세요.")
        return self._app

    def invoke(self, question: str) -> dict:
        """워크플로우 실행"""
        return self.app.invoke({
            "question": question,
            "optimized_queries": [],
            "retrieved_docs": [],
            "final_answer": ""
        })
