from typing import Any, Callable, List, Type

from mcp_agent.agents.agent import Agent
from mcp_agent.executor.executor import Executor
from mcp_agent.workflows.llm.augmented_llm import (
    AugmentedLLM,
    MessageParamT,
    MessageT,
    ModelT,
)
from mcp_agent.workflows.parallel.fan_in import FanInInput, FanInLLM
from mcp_agent.workflows.parallel.fan_out import FanOut


class ParallelLLM(AugmentedLLM[MessageParamT, MessageT]):
    """
    LLMs can sometimes work simultaneously on a task (fan-out)
    and have their outputs aggregated programmatically (fan-in).
    This workflow performs both the fan-out and fan-in operations using  LLMs.
    From the user's perspective, an input is specified and the output is returned.

    When to use this workflow:
        Parallelization is effective when the divided subtasks can be parallelized
        for speed (sectioning), or when multiple perspectives or attempts are needed for
        higher confidence results (voting).

    Examples:
        Sectioning:
            - Implementing guardrails where one model instance processes user queries
            while another screens them for inappropriate content or requests.

            - Automating evals for evaluating LLM performance, where each LLM call
            evaluates a different aspect of the model’s performance on a given prompt.

        Voting:
            - Reviewing a piece of code for vulnerabilities, where several different
            agents review and flag the code if they find a problem.

            - Evaluating whether a given piece of content is inappropriate,
            with multiple agents evaluating different aspects or requiring different
            vote thresholds to balance false positives and negatives.
    """

    def __init__(
        self,
        fan_in_agent: Agent | AugmentedLLM | Callable[[FanInInput], Any],
        fan_out_agents: List[Agent | AugmentedLLM] | None = None,
        fan_out_functions: List[Callable] | None = None,
        llm_factory: Callable[[Agent], AugmentedLLM] = None,
        executor: Executor | None = None,
    ):
        """
        Initialize the LLM with a list of server names and an instruction.
        If a name is provided, it will be used to identify the LLM.
        If an agent is provided, all other properties are optional
        """
        super().__init__(executor=executor)

        self.llm_factory = llm_factory
        self.fan_in_agent = fan_in_agent
        self.fan_out_agents = fan_out_agents
        self.fan_out_functions = fan_out_functions
        self.history = (
            None  # History tracking is complex in this workflow, so it is not supported
        )

        if isinstance(fan_in_agent, Callable):
            self.fan_in_fn = fan_in_agent
        else:
            self.fan_in = FanInLLM(
                aggregator_agent=fan_in_agent,
                llm_factory=llm_factory,
                executor=executor,
            )

        self.fan_out = FanOut(
            agents=fan_out_agents,
            functions=fan_out_functions,
            llm_factory=llm_factory,
            executor=executor,
        )

    async def generate(
        self,
        message: str | MessageParamT | List[MessageParamT],
        use_history: bool = True,
        max_iterations: int = 10,
        model: str = None,
        stop_sequences: List[str] = None,
        max_tokens: int = 2048,
        parallel_tool_calls: bool = True,
    ) -> List[MessageT] | Any:
        # First, we fan-out
        responses = await self.fan_out.generate(
            message=message,
            use_history=use_history,
            max_iterations=max_iterations,
            model=model,
            stop_sequences=stop_sequences,
            max_tokens=max_tokens,
            parallel_tool_calls=parallel_tool_calls,
        )

        # Then, we fan-in
        if self.fan_in_fn:
            result = await self.fan_in_fn(responses)
        else:
            result = await self.fan_in.generate(
                messages=responses,
                use_history=use_history,
                max_iterations=max_iterations,
                model=model,
                stop_sequences=stop_sequences,
                max_tokens=max_tokens,
                parallel_tool_calls=parallel_tool_calls,
            )

        return result

    async def generate_str(
        self,
        message: str | MessageParamT | List[MessageParamT],
        use_history: bool = True,
        max_iterations: int = 10,
        model: str = None,
        stop_sequences: List[str] = None,
        max_tokens: int = 2048,
        parallel_tool_calls: bool = True,
    ) -> str:
        """Request an LLM generation and return the string representation of the result"""

        # First, we fan-out
        responses = await self.fan_out.generate(
            message=message,
            use_history=use_history,
            max_iterations=max_iterations,
            model=model,
            stop_sequences=stop_sequences,
            max_tokens=max_tokens,
            parallel_tool_calls=parallel_tool_calls,
        )

        # Then, we fan-in
        if self.fan_in_fn:
            result = str(await self.fan_in_fn(responses))
        else:
            result = await self.fan_in.generate_str(
                messages=responses,
                use_history=use_history,
                max_iterations=max_iterations,
                model=model,
                stop_sequences=stop_sequences,
                max_tokens=max_tokens,
                parallel_tool_calls=parallel_tool_calls,
            )
        return result

    async def generate_structured(
        self,
        message: str | MessageParamT | List[MessageParamT],
        response_model: Type[ModelT],
        use_history: bool = True,
        max_iterations: int = 10,
        model: str = None,
        stop_sequences: List[str] = None,
        max_tokens: int = 2048,
        parallel_tool_calls: bool = True,
    ) -> ModelT:
        """Request a structured LLM generation and return the result as a Pydantic model."""
        # First, we fan-out
        responses = await self.fan_out.generate(
            message=message,
            use_history=use_history,
            max_iterations=max_iterations,
            model=model,
            stop_sequences=stop_sequences,
            max_tokens=max_tokens,
            parallel_tool_calls=parallel_tool_calls,
        )

        # Then, we fan-in
        if self.fan_in_fn:
            result = await self.fan_in_fn(responses)
        else:
            result = await self.fan_in.generate_structured(
                messages=responses,
                response_model=response_model,
                use_history=use_history,
                max_iterations=max_iterations,
                model=model,
                stop_sequences=stop_sequences,
                max_tokens=max_tokens,
                parallel_tool_calls=parallel_tool_calls,
            )
        return result