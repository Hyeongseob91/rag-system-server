"""RAG Workflow - LangGraph"""
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from ..schemas import RAGState, RouteQuery
from ..nodes import QueryRewriteNode, RetrieverNode, GeneratorNode, SimpleGeneratorNode
from ..services import LLMService
from ..prompts import ROUTER_SYSTEM_PROMPT


class RAGWorkflow:
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
        print(f"--- [Router] 질문 분석 중: {state['question']} ---")
        llm = self._llm_service.get_rewrite_llm()
        prompt = ChatPromptTemplate.from_messages([("system", ROUTER_SYSTEM_PROMPT), ("human", "{question}")])
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
        workflow = StateGraph(RAGState)
        workflow.add_node(self._query_rewrite_node.name, self._query_rewrite_node)
        workflow.add_node(self._retriever_node.name, self._retriever_node)
        workflow.add_node(self._generator_node.name, self._generator_node)
        workflow.add_node(self._simple_generator_node.name, self._simple_generator_node)

        workflow.set_conditional_entry_point(
            self.route_question,
            {self._query_rewrite_node.name: self._query_rewrite_node.name, self._simple_generator_node.name: self._simple_generator_node.name}
        )
        workflow.add_edge(self._query_rewrite_node.name, self._retriever_node.name)
        workflow.add_edge(self._retriever_node.name, self._generator_node.name)
        workflow.add_edge(self._generator_node.name, END)
        workflow.add_edge(self._simple_generator_node.name, END)
        self._app = workflow.compile()
        return self

    @property
    def app(self):
        if self._app is None:
            raise RuntimeError("Workflow가 빌드되지 않았습니다. build()를 먼저 호출하세요.")
        return self._app

    def invoke(self, question: str) -> dict:
        return self.app.invoke({"question": question, "optimized_queries": [], "retrieved_docs": [], "final_answer": ""})
