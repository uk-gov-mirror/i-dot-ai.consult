<script lang="ts">
  import { tick, untrack } from "svelte";
  import { SvelteMap, SvelteSet } from "svelte/reactivity";

  import Alert from "../../Alert/Alert.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import Select from "../../inputs/Select/Select.svelte";
  import StepTitle from "../StepTitle/StepTitle.svelte";
  import Checklist from "../../svg/material/Checklist.svelte";
  import ErrorIcon from "../../svg/material/Error.svelte";
  import QuestionTypeRow from "./QuestionTypeRow.svelte";

  import {
    buildQuestionsV2Query,
    buildQuestionV2UpdateQuery,
  } from "../../../global/queries/questions/queries";
  import type {
    QuestionV2,
    QuestionV2UpdateBody,
  } from "../../../global/queries/questions/types";
  import {
    getApiQuestionResponsesUrl,
    getDataUploadDeleteQuestionsUrl,
    getDataUploadFinaliseUrl,
  } from "../../../global/routes";

  interface Props {
    consultationId: string;
  }

  let { consultationId }: Props = $props();

  const PAGE_SIZES = [10, 20, 50];

  const questionsQuery = buildQuestionsV2Query(untrack(() => consultationId));

  let questions: QuestionV2[] = $derived(questionsQuery.query.data ?? []);
  let openQuestions = $derived(
    questions.filter((question) => question.type === "open"),
  );
  let linkedByClosedId = $derived.by(() => {
    const map = new SvelteMap<string, QuestionV2[]>();
    for (const open of openQuestions) {
      if (!open.closed_question) continue;
      map.set(open.closed_question, [
        ...(map.get(open.closed_question) ?? []),
        open,
      ]);
    }
    return map;
  });

  const REFERS_BACK =
    /(please )?(explain|say why|tell us why|give (your )?reasons)|why (did|do) you|if (so|not|yes)|if you answered|please (expand|elaborate|comment)|what (was|were) your reason/i;
  const rejectedProposals = new SvelteSet<string>();
  let proposedByClosedId = $derived.by(() => {
    const map = new SvelteMap<string, QuestionV2>();
    questions.forEach((question, index) => {
      const next = questions[index + 1];
      if (
        question.type === "closed" &&
        next?.type === "open" &&
        !next.closed_question &&
        !linkedByClosedId.has(question.id) &&
        !rejectedProposals.has(question.id) &&
        REFERS_BACK.test(next.text.trim())
      ) {
        map.set(question.id, next);
      }
    });
    return map;
  });

  let typeCounts = $derived({
    open: openQuestions.length,
    closed: questions.filter((question) => question.type === "closed").length,
    hybrid: linkedByClosedId.size,
    demographic: questions.filter((question) => question.type === "demographic")
      .length,
  });
  let summary = $derived(
    [
      `${questions.length} ${questions.length === 1 ? "question" : "questions"}`,
      typeCounts.open && `${typeCounts.open} open`,
      typeCounts.closed - typeCounts.hybrid &&
        `${typeCounts.closed - typeCounts.hybrid} closed`,
      typeCounts.hybrid && `${typeCounts.hybrid} hybrid`,
      typeCounts.demographic && `${typeCounts.demographic} demographic`,
    ]
      .filter(Boolean)
      .join(" · "),
  );

  const changedIds = new SvelteSet<string>();
  let changedCount = $derived(
    questions.filter((question) => changedIds.has(question.id)).length,
  );
  let sortMode = $state<"file" | "changed">("file");
  let orderedQuestions = $derived(
    sortMode === "changed"
      ? [...questions].sort(
          (first, second) =>
            Number(changedIds.has(second.id)) -
              Number(changedIds.has(first.id)) || first.number - second.number,
        )
      : questions,
  );

  let pageSize = $state(PAGE_SIZES[0]);
  let currentPage = $state(1);
  let totalPages = $derived(
    Math.max(1, Math.ceil(questions.length / pageSize)),
  );
  let pageStart = $derived((currentPage - 1) * pageSize);
  let pageEnd = $derived(Math.min(pageStart + pageSize, questions.length));
  let pageQuestions = $derived(orderedQuestions.slice(pageStart, pageEnd));

  let saveError = $state("");
  let continueError = $state("");
  let continueErrorEl = $state<HTMLElement | null>(null);
  let linking = $state<string | null>(null);
  let editing = $state<string | null>(null);
  let saving = $state(false);

  const answerSamples = new SvelteMap<string, string[]>();
  const answersFailed = new SvelteSet<string>();

  async function fetchAnswerSample(questionId: string) {
    if (answerSamples.has(questionId)) return;
    answersFailed.delete(questionId);
    const url = `${getApiQuestionResponsesUrl(consultationId, questionId)}?page_size=3`;
    try {
      const response = await fetch(url);
      if (!response.ok) {
        answersFailed.add(questionId);
        return;
      }
      const data = await response.json();
      answerSamples.set(
        questionId,
        (data.all_respondents ?? []).map(
          (respondent: { free_text_answer_text: string }) =>
            respondent.free_text_answer_text,
        ),
      );
    } catch {
      answersFailed.add(questionId);
    }
  }

  const update = buildQuestionV2UpdateQuery(
    untrack(() => consultationId),
    async () => {
      saveError = "";
      await questionsQuery.fetch();
    },
    async () => {
      saving = false;
    },
  );

  async function handleSave(questionId: string, body: QuestionV2UpdateBody) {
    const question = questions.find((entry) => entry.id === questionId);
    saving = true;
    continueError = "";
    try {
      await update.fetch(questionId, body);
      changedIds.add(questionId);
      return true;
    } catch (error) {
      console.error(error);
      saveError = `Question ${question?.number} was not saved. Try again.`;
      return false;
    } finally {
      saving = false;
    }
  }

  function setPage(page: number) {
    currentPage = Math.min(Math.max(page, 1), totalPages);
  }

  async function handleContinue() {
    if (openQuestions.length === 0) {
      continueError =
        "No question is set to open, so there will be no themes to sign off.";
      await tick();
      continueErrorEl?.focus();
      return;
    }
    window.location.href = getDataUploadFinaliseUrl(consultationId);
  }
</script>

<StepTitle
  stepNo={5}
  maxStepNo={6}
  title="Review your questions"
  Icon={Checklist}
/>

<p class="mt-3.5 mb-6 text-md leading-relaxed text-neutral-500">
  There are {questions.length} questions and each has been categorised as either closed,
  open or hybrid. Open questions will have themes assigned and closed questions have
  fixed answers. Double check that the questions have been categorised correctly.
</p>

{#if continueError}
  <div class="mb-6" role="alert" tabindex="-1" bind:this={continueErrorEl}>
    <Alert variant="error" Icon={ErrorIcon}>
      <p class="font-bold">There is a problem</p>
      <p>{continueError}</p>
    </Alert>
  </div>
{/if}

{#if saveError}
  <div class="mb-6" role="alert">
    <Alert variant="error" onTimeout={() => (saveError = "")}>{saveError}</Alert
    >
  </div>
{/if}

<div class="questions-panel rounded-xl border border-neutral-300 bg-white">
  {#if questionsQuery.query.isPending}
    <div class="px-7 py-4 text-md text-neutral-500">Loading questions...</div>
  {:else if questionsQuery.query.isError}
    <div class="px-7 py-4 text-md text-neutral-500">
      Failed to load questions.
    </div>
  {:else}
    <div
      class="flex flex-wrap items-baseline justify-between gap-3 px-7 pt-4 pb-3"
    >
      <p class="text-md text-neutral-500">{summary}</p>
      <div class="flex flex-wrap items-center gap-4">
        <p class="text-sm text-neutral-500" aria-live="polite">
          {changedCount === 0
            ? "Nothing changed yet"
            : changedCount === 1
              ? "1 question changed in total"
              : `${changedCount} questions changed in total`}
        </p>
        <div class="sort-select">
          <Select
            id="review-questions-sort"
            label={{ text: "Sort", horizontal: true }}
            items={[
              { value: "file", label: "File order" },
              { value: "changed", label: "Changed first" },
            ]}
            value={sortMode}
            onchange={(value) => {
              sortMode = value === "changed" ? "changed" : "file";
              currentPage = 1;
            }}
          />
        </div>
      </div>
    </div>
    <p class="px-7 pb-4 text-sm text-neutral-500">
      Every change made here is tracked, listed before the analysis starts, and
      saved to the consultation afterwards. There is no need to keep note of
      them.
    </p>
  {/if}

  {#if !questionsQuery.query.isPending && !questionsQuery.query.isError}
    <div class="border-t border-neutral-200">
      <div class="flex gap-4 px-7 py-2 text-sm text-neutral-500">
        <span class="w-16 shrink-0">No.</span>
        <span class="flex-1">Question</span>
        <span class="w-52 shrink-0">What kind of question it is</span>
        <span class="w-16 shrink-0"><span class="sr-only">Actions</span></span>
      </div>

      {#each pageQuestions as question (question.id)}
        <QuestionTypeRow
          {question}
          linkedQuestions={linkedByClosedId.get(question.id) ?? []}
          {openQuestions}
          proposed={proposedByClosedId.get(question.id)}
          linking={linking === question.id}
          editing={editing === question.id}
          {saving}
          answers={answerSamples.get(question.id)}
          answersFailed={answersFailed.has(question.id)}
          onStartLinking={() => (linking = question.id)}
          onCancelLinking={() => (linking = null)}
          onStartEditing={() => (editing = question.id)}
          onCancelEditing={() => (editing = null)}
          onShowAnswers={() => fetchAnswerSample(question.id)}
          onRejectProposal={() => rejectedProposals.add(question.id)}
          onSave={handleSave}
        />
      {/each}
    </div>

    {#if questions.length > PAGE_SIZES[0]}
      <div
        class="flex flex-wrap items-center justify-between gap-4 border-t border-neutral-200 px-7 py-4"
      >
        <p class="text-sm text-neutral-500" aria-live="polite">
          Showing {pageStart + 1} to {pageEnd} of {questions.length}
        </p>
        <nav aria-label="Question pages" class="flex items-center gap-1">
          <Button
            size="xs"
            variant="ghost"
            disabled={currentPage === 1}
            ariaLabel="Previous page"
            handleClick={() => setPage(currentPage - 1)}
          >
            Previous
          </Button>
          <span class="px-2 text-xs text-neutral-600" aria-current="page">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            size="xs"
            variant="ghost"
            disabled={currentPage === totalPages}
            ariaLabel="Next page"
            handleClick={() => setPage(currentPage + 1)}
          >
            Next
          </Button>
        </nav>
        <div class="page-size text-xs">
          <Select
            id="review-questions-page-size"
            label={{ text: "Per page", horizontal: true }}
            items={PAGE_SIZES.map((size) => ({
              value: size.toString(),
              label: size.toString(),
            }))}
            value={pageSize.toString()}
            onchange={(value) => {
              if (value === undefined) return;
              pageSize = Number.parseInt(value);
              currentPage = 1;
            }}
          />
        </div>
      </div>
    {/if}
  {/if}
</div>

<div class="mt-7 flex flex-wrap justify-between gap-2">
  <Button size="sm" href={getDataUploadDeleteQuestionsUrl(consultationId)}>
    Back
  </Button>
  <Button size="sm" variant="primary" handleClick={handleContinue}>
    Continue to closed questions
  </Button>
</div>

<style>
  @reference "../../../styles/global.css";

  .page-size :global(label) {
    @apply text-xs;
  }

  .sort-select :global(label) {
    @apply text-sm text-neutral-500 md:text-sm;
  }

  .questions-panel :global(select) {
    @apply rounded-md;
  }
</style>
