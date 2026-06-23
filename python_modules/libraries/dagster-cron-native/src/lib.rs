use chrono::{DateTime, FixedOffset, LocalResult, NaiveDateTime, TimeDelta, TimeZone, Utc};
use chrono_tz::Tz;
use cron::{
    CronScheduleParts, DayOfWeekNumbering, DowDomOperand, NonexistentTimeBehavior,
    OwnedScheduleIterator, Schedule,
};
use pyo3::conversion::IntoPyObject;
use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyAny;

const DAGSTER_SEARCH_YEARS: i64 = 400;

#[pyclass(
    name = "ScheduleParts",
    module = "dagster_cron_native",
    eq,
    eq_int,
    rename_all = "SCREAMING_SNAKE_CASE"
)]
#[derive(Clone, Copy, PartialEq)]
enum PyCronScheduleParts {
    Five,
    Six,
    Seven,
    FiveOrSix,
    SixOrSeven,
    All,
}

impl From<PyCronScheduleParts> for CronScheduleParts {
    fn from(value: PyCronScheduleParts) -> Self {
        match value {
            PyCronScheduleParts::Five => Self::Five,
            PyCronScheduleParts::Six => Self::Six,
            PyCronScheduleParts::Seven => Self::Seven,
            PyCronScheduleParts::FiveOrSix => Self::FiveOrSix,
            PyCronScheduleParts::SixOrSeven => Self::SixOrSeven,
            PyCronScheduleParts::All => Self::All,
        }
    }
}

#[pyclass(
    name = "DayMatching",
    module = "dagster_cron_native",
    eq,
    eq_int,
    rename_all = "SCREAMING_SNAKE_CASE"
)]
#[derive(Clone, Copy, PartialEq)]
enum PyDayMatching {
    And,
    Or,
}

impl From<PyDayMatching> for DowDomOperand {
    fn from(value: PyDayMatching) -> Self {
        match value {
            PyDayMatching::And => Self::And,
            PyDayMatching::Or => Self::Or,
        }
    }
}

#[pyclass(
    name = "DayOfWeekNumbering",
    module = "dagster_cron_native",
    eq,
    eq_int,
    rename_all = "SCREAMING_SNAKE_CASE"
)]
#[derive(Clone, Copy, PartialEq)]
enum PyDayOfWeekNumbering {
    OneIndexed,
    ZeroIndexed,
}

impl From<PyDayOfWeekNumbering> for DayOfWeekNumbering {
    fn from(value: PyDayOfWeekNumbering) -> Self {
        match value {
            PyDayOfWeekNumbering::OneIndexed => Self::OneIndexed,
            PyDayOfWeekNumbering::ZeroIndexed => Self::ZeroIndexed,
        }
    }
}

#[pyclass(
    name = "NonexistentTimeBehavior",
    module = "dagster_cron_native",
    eq,
    eq_int,
    rename_all = "SCREAMING_SNAKE_CASE"
)]
#[derive(Clone, Copy, PartialEq)]
enum PyNonexistentTimeBehavior {
    Skip,
    NextExistent,
}

impl From<PyNonexistentTimeBehavior> for NonexistentTimeBehavior {
    fn from(value: PyNonexistentTimeBehavior) -> Self {
        match value {
            PyNonexistentTimeBehavior::Skip => Self::Skip,
            PyNonexistentTimeBehavior::NextExistent => Self::NextExistent,
        }
    }
}

#[pyclass(name = "Schedule", module = "dagster_cron_native")]
#[derive(Clone)]
struct PySchedule {
    schedule: Schedule,
}

#[pymethods]
impl PySchedule {
    #[new]
    #[pyo3(signature = (
        expression,
        parts = PyCronScheduleParts::All,
        day_matching = PyDayMatching::And,
        search_years = None,
        day_of_week_numbering = PyDayOfWeekNumbering::OneIndexed,
        wraparound_ranges = false,
        last_specifiers = false,
        nearest_weekday = false,
        nth_weekday_of_month = false,
        random_fields = false,
        nonexistent_time_behavior = PyNonexistentTimeBehavior::Skip,
    ))]
    fn new(
        expression: &str,
        parts: PyCronScheduleParts,
        day_matching: PyDayMatching,
        search_years: Option<i64>,
        day_of_week_numbering: PyDayOfWeekNumbering,
        wraparound_ranges: bool,
        last_specifiers: bool,
        nearest_weekday: bool,
        nth_weekday_of_month: bool,
        random_fields: bool,
        nonexistent_time_behavior: PyNonexistentTimeBehavior,
    ) -> PyResult<Self> {
        let mut builder = Schedule::builder()
            .allowed_cron_schedule_parts(parts.into())
            .day_of_week_numbering(day_of_week_numbering.into())
            .dow_dom_operand(day_matching.into())
            .wraparound_ranges(wraparound_ranges)
            .last_specifiers(last_specifiers)
            .nearest_weekday(nearest_weekday)
            .nth_weekday_of_month(nth_weekday_of_month)
            .random_fields(random_fields)
            .nonexistent_time_behavior(nonexistent_time_behavior.into());

        if let Some(years) = search_years {
            builder = builder.search_interval(TimeDelta::days(years.max(1) * 366));
        }

        let schedule = builder
            .parse(expression)
            .map_err(|err| PyValueError::new_err(err.to_string()))?;

        Ok(Self { schedule })
    }

    fn source(&self) -> &str {
        self.schedule.source()
    }

    #[pyo3(signature = (start_time = None))]
    fn iter(&self, start_time: Option<Bound<'_, PyAny>>) -> PyResult<PyScheduleIterator> {
        let start = PyDateTimeState::extract(start_time.as_ref())?;
        Ok(PyScheduleIterator {
            inner: start.into_iterator(self.schedule.clone()),
        })
    }

    fn includes(&self, moment: Bound<'_, PyAny>) -> PyResult<bool> {
        Ok(PyDateTimeState::extract(Some(&moment))?.is_included_in(&self.schedule))
    }
}

#[pyclass(name = "ScheduleIterator", module = "dagster_cron_native")]
struct PyScheduleIterator {
    inner: NativeIterator,
}

#[pymethods]
impl PyScheduleIterator {
    fn current(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        self.inner.current_to_py(py)
    }

    fn next(&mut self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        if !self.inner.next() {
            return Err(PyValueError::new_err("failed to find next date"));
        }
        self.inner.current_to_py(py)
    }

    fn previous(&mut self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        if !self.inner.previous() {
            return Err(PyValueError::new_err("failed to find previous date"));
        }
        self.inner.current_to_py(py)
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        if !self.inner.next() {
            return Ok(None);
        }
        Ok(Some(self.inner.current_to_py(py)?))
    }
}

#[pyclass(name = "CronStringIterator", module = "dagster_cron_native")]
struct PyCronStringIterator {
    iter: OwnedScheduleIterator<Tz>,
    ascending: bool,
    repeats_every_hour: bool,
}

#[pymethods]
impl PyCronStringIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        loop {
            let next = if self.ascending {
                self.iter.next()
            } else {
                self.iter.next_back()
            };

            let Some(next) = next else {
                return Ok(None);
            };

            if !self.repeats_every_hour && is_pre_transition_ambiguous(&next) {
                continue;
            }

            return Ok(Some(datetime_to_py(py, &next, DateTimeKind::Aware)?));
        }
    }
}

#[pyfunction]
fn is_valid_cron_string(cron_string: &str) -> bool {
    new_dagster_schedule(cron_string).is_ok()
}

#[pyfunction]
fn repeats_every_hour(cron_string: &str) -> PyResult<bool> {
    new_dagster_schedule(cron_string)?;
    dagster_repeats_every_hour(cron_string)
}

#[pyfunction]
#[pyo3(signature = (
    start_timestamp,
    cron_string,
    execution_timezone = None,
    ascending = true,
    start_offset = 0,
))]
fn cron_string_iterator(
    start_timestamp: f64,
    cron_string: &str,
    execution_timezone: Option<&str>,
    ascending: bool,
    start_offset: i64,
) -> PyResult<PyCronStringIterator> {
    if start_offset > 0 {
        return Err(PyValueError::new_err("start_offset must be <= 0"));
    }

    let schedule = new_dagster_schedule(cron_string)?;
    let timezone_name = execution_timezone.unwrap_or("UTC");
    let timezone = timezone_name
        .parse::<Tz>()
        .map_err(|_| PyValueError::new_err(format!("Unknown timezone: {timezone_name}")))?;
    let start = datetime_from_timestamp(start_timestamp)?.with_timezone(&timezone);

    let mut anchor_iter = schedule.clone().after_owned(start);
    let anchor_steps = (-start_offset + 1) as usize;
    let mut anchor = start;
    for _ in 0..anchor_steps {
        let next_anchor = if ascending {
            anchor_iter.next_back()
        } else {
            anchor_iter.next()
        };
        anchor = next_anchor.ok_or_else(|| PyValueError::new_err("failed to find anchor date"))?;
    }

    Ok(PyCronStringIterator {
        iter: schedule.after_owned(anchor),
        ascending,
        repeats_every_hour: dagster_repeats_every_hour(cron_string)?,
    })
}

fn dagster_repeats_every_hour(cron_string: &str) -> PyResult<bool> {
    let normalized = normalize_dagster_expression(cron_string)?;
    let Some(tokens) = field_tokens(&normalized) else {
        return Ok(normalized == "@hourly");
    };

    Ok(tokens.get(1).is_some_and(|hour| *hour == "*"))
}

fn is_pre_transition_ambiguous(datetime: &DateTime<Tz>) -> bool {
    match datetime
        .timezone()
        .from_local_datetime(&datetime.naive_local())
    {
        LocalResult::Ambiguous(earliest, latest) => {
            earliest.timestamp() != latest.timestamp()
                && datetime.timestamp() == earliest.timestamp()
        }
        _ => false,
    }
}

fn new_dagster_schedule(expression: &str) -> PyResult<Schedule> {
    let expression = normalize_dagster_expression(expression)?;

    if field_tokens(&expression).is_none() && !expression.starts_with('@') {
        return Err(PyValueError::new_err(
            "Dagster cron schedules must have exactly 5 fields",
        ));
    }

    dagster_schedule_builder(DowDomOperand::And)
        .parse(&expression)
        .map_err(|err| PyValueError::new_err(err.to_string()))?;

    dagster_schedule_builder(DowDomOperand::Or)
        .parse(&expression)
        .map_err(|err| PyValueError::new_err(err.to_string()))
}

fn dagster_schedule_builder(day_matching: DowDomOperand) -> cron::ScheduleConfigBuilder {
    Schedule::builder()
        .allowed_cron_schedule_parts(CronScheduleParts::Five)
        .day_of_week_numbering(DayOfWeekNumbering::ZeroIndexed)
        .dow_dom_operand(day_matching)
        .wraparound_ranges(true)
        .last_specifiers(true)
        .nearest_weekday(true)
        .nth_weekday_of_month(true)
        .random_fields(true)
        .nonexistent_time_behavior(NonexistentTimeBehavior::NextExistent)
        .search_interval(TimeDelta::days(DAGSTER_SEARCH_YEARS * 366))
}

fn normalize_dagster_expression(expression: &str) -> PyResult<String> {
    let trimmed = expression.trim();
    if trimmed.is_empty() {
        return Err(PyValueError::new_err("Cron expression is empty"));
    }

    if let Some(alias) = trimmed.strip_prefix('@') {
        let normalized = match alias.to_ascii_lowercase().as_str() {
            "annually" => "@yearly",
            "midnight" => "@daily",
            "hourly" => "@hourly",
            "daily" => "@daily",
            "weekly" => "@weekly",
            "monthly" => "@monthly",
            "yearly" => "@yearly",
            "reboot" => return Err(PyValueError::new_err("@reboot is not supported")),
            _ => trimmed,
        };
        return Ok(normalized.to_string());
    }

    match field_tokens(trimmed) {
        Some(tokens) if tokens.len() == 5 => Ok(trimmed.to_string()),
        _ => Err(PyValueError::new_err(
            "Dagster cron schedules must have exactly 5 fields",
        )),
    }
}

fn field_tokens(expression: &str) -> Option<Vec<&str>> {
    if expression.starts_with('@') {
        return None;
    }
    Some(expression.split_whitespace().collect())
}

fn datetime_from_timestamp(timestamp: f64) -> PyResult<DateTime<Utc>> {
    if !timestamp.is_finite() {
        return Err(PyValueError::new_err("timestamp must be finite"));
    }

    let mut seconds = timestamp.floor() as i64;
    let mut nanoseconds = ((timestamp - seconds as f64) * 1_000_000_000.0).round() as u32;
    if nanoseconds == 1_000_000_000 {
        seconds += 1;
        nanoseconds = 0;
    }

    DateTime::from_timestamp(seconds, nanoseconds)
        .ok_or_else(|| PyValueError::new_err("timestamp is out of range"))
}

enum PyDateTimeState {
    NaiveUtc(DateTime<Utc>),
    AwareUtc(DateTime<Utc>),
    FixedOffset(DateTime<FixedOffset>),
    ChronoTz(DateTime<Tz>),
}

impl PyDateTimeState {
    fn extract(value: Option<&Bound<'_, PyAny>>) -> PyResult<Self> {
        let Some(value) = value else {
            return Ok(Self::AwareUtc(Utc::now()));
        };

        if value.is_none() {
            return Ok(Self::AwareUtc(Utc::now()));
        }

        if let Ok(datetime) = value.extract::<DateTime<Tz>>() {
            return Ok(Self::ChronoTz(datetime));
        }

        if let Ok(datetime) = value.extract::<DateTime<Utc>>() {
            return Ok(Self::AwareUtc(datetime));
        }

        if let Ok(datetime) = value.extract::<DateTime<FixedOffset>>() {
            return Ok(Self::FixedOffset(datetime));
        }

        if let Ok(datetime) = value.extract::<NaiveDateTime>() {
            return Ok(Self::NaiveUtc(datetime.and_utc()));
        }

        Err(PyTypeError::new_err(
            "start_time must be a datetime or None",
        ))
    }

    fn into_iterator(self, schedule: Schedule) -> NativeIterator {
        match self {
            Self::NaiveUtc(datetime) => NativeIterator::NaiveUtc {
                last: datetime,
                iter: schedule.after_owned(datetime),
            },
            Self::AwareUtc(datetime) => NativeIterator::AwareUtc {
                last: datetime,
                iter: schedule.after_owned(datetime),
            },
            Self::FixedOffset(datetime) => NativeIterator::FixedOffset {
                last: datetime,
                iter: schedule.after_owned(datetime),
            },
            Self::ChronoTz(datetime) => NativeIterator::ChronoTz {
                last: datetime,
                iter: schedule.after_owned(datetime),
            },
        }
    }

    fn is_included_in(self, schedule: &Schedule) -> bool {
        match self {
            Self::NaiveUtc(datetime) | Self::AwareUtc(datetime) => schedule.includes(datetime),
            Self::FixedOffset(datetime) => schedule.includes(datetime),
            Self::ChronoTz(datetime) => schedule.includes(datetime),
        }
    }
}

enum NativeIterator {
    NaiveUtc {
        iter: OwnedScheduleIterator<Utc>,
        last: DateTime<Utc>,
    },
    AwareUtc {
        iter: OwnedScheduleIterator<Utc>,
        last: DateTime<Utc>,
    },
    FixedOffset {
        iter: OwnedScheduleIterator<FixedOffset>,
        last: DateTime<FixedOffset>,
    },
    ChronoTz {
        iter: OwnedScheduleIterator<Tz>,
        last: DateTime<Tz>,
    },
}

impl NativeIterator {
    fn next(&mut self) -> bool {
        match self {
            Self::NaiveUtc { iter, last } | Self::AwareUtc { iter, last } => {
                advance_forward(iter, last)
            }
            Self::FixedOffset { iter, last } => advance_forward(iter, last),
            Self::ChronoTz { iter, last } => advance_forward(iter, last),
        }
    }

    fn previous(&mut self) -> bool {
        match self {
            Self::NaiveUtc { iter, last } | Self::AwareUtc { iter, last } => {
                advance_backward(iter, last)
            }
            Self::FixedOffset { iter, last } => advance_backward(iter, last),
            Self::ChronoTz { iter, last } => advance_backward(iter, last),
        }
    }

    fn current_to_py(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        match self {
            Self::NaiveUtc { last, .. } => datetime_to_py(py, last, DateTimeKind::Naive),
            Self::AwareUtc { last, .. } => datetime_to_py(py, last, DateTimeKind::Aware),
            Self::FixedOffset { last, .. } => datetime_to_py(py, last, DateTimeKind::Aware),
            Self::ChronoTz { last, .. } => datetime_to_py(py, last, DateTimeKind::Aware),
        }
    }
}

fn advance_forward<Z>(iter: &mut OwnedScheduleIterator<Z>, last: &mut DateTime<Z>) -> bool
where
    Z: TimeZone + 'static,
{
    let Some(next) = iter.next() else {
        return false;
    };
    *last = next;
    true
}

fn advance_backward<Z>(iter: &mut OwnedScheduleIterator<Z>, last: &mut DateTime<Z>) -> bool
where
    Z: TimeZone + 'static,
{
    let Some(previous) = iter.next_back() else {
        return false;
    };
    *last = previous;
    true
}

#[derive(Clone, Copy)]
enum DateTimeKind {
    Naive,
    Aware,
}

fn datetime_to_py<'py, Z>(
    py: Python<'py>,
    datetime: &DateTime<Z>,
    datetime_kind: DateTimeKind,
) -> PyResult<Py<PyAny>>
where
    Z: TimeZone + IntoPyObject<'py>,
{
    match datetime_kind {
        DateTimeKind::Naive => Ok(datetime.naive_utc().into_pyobject(py)?.into_any().unbind()),
        DateTimeKind::Aware => Ok(datetime.into_pyobject(py)?.into_any().unbind()),
    }
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PySchedule>()?;
    module.add_class::<PyScheduleIterator>()?;
    module.add_class::<PyCronStringIterator>()?;
    module.add_class::<PyCronScheduleParts>()?;
    module.add_class::<PyDayMatching>()?;
    module.add_class::<PyDayOfWeekNumbering>()?;
    module.add_class::<PyNonexistentTimeBehavior>()?;
    module.add_function(wrap_pyfunction!(cron_string_iterator, module)?)?;
    module.add_function(wrap_pyfunction!(is_valid_cron_string, module)?)?;
    module.add_function(wrap_pyfunction!(repeats_every_hour, module)?)?;
    Ok(())
}
