from __future__ import annotations

import functools
import inspect
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Callable

from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode

_tracer: trace.Tracer | None = None


def get_tracer() -> trace.Tracer:
    if _tracer is not None:
        return _tracer
    return trace.get_tracer(__name__)


@contextmanager
def create_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> Iterator[trace.Span]:
    tracer = get_tracer()
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        try:
            yield span
        except Exception as exc:
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise


def observe(
    fn: Callable | str | None = None,
    /,
    *,
    name: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    record_args: bool = False,
    record_result: bool = False,
    **span_attrs: Any,
):
    if callable(fn):
        return _wrap(
            fn,
            span_name=None,
            kind=kind,
            record_args=record_args,
            record_result=record_result,
            span_attrs=span_attrs,
        )

    if isinstance(fn, str):
        _name = fn

        def decorator(f: Callable) -> Callable:
            return _wrap(
                f,
                span_name=_name,
                kind=kind,
                record_args=record_args,
                record_result=record_result,
                span_attrs=span_attrs,
            )

        return decorator

    def decorator(f: Callable) -> Callable:
        return _wrap(
            f,
            span_name=name,
            kind=kind,
            record_args=record_args,
            record_result=record_result,
            span_attrs=span_attrs,
        )

    return decorator


def _wrap(
    fn: Callable,
    *,
    span_name: str | None,
    kind: SpanKind,
    record_args: bool,
    record_result: bool,
    span_attrs: dict[str, Any],
) -> Callable:
    resolved_name = span_name or f"{fn.__module__}.{fn.__qualname__}"
    sig = inspect.signature(fn) if record_args else None

    def _build_attrs(args: tuple, kwargs: dict) -> dict[str, Any]:
        attrs = dict(span_attrs)
        if sig is None:
            return attrs
        try:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for param, value in bound.arguments.items():
                if param in ("self", "cls"):
                    continue
                try:
                    str_val = str(value)
                    if len(str_val) <= 200:
                        attrs[f"arg.{param}"] = str_val
                except Exception:
                    pass
        except Exception:
            pass
        return attrs

    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            attrs = _build_attrs(args, kwargs)
            with create_span(
                resolved_name, kind=kind, attributes=attrs or None
            ) as span:
                result = await fn(*args, **kwargs)
                if record_result:
                    try:
                        span.set_attribute("result", str(result)[:200])
                    except Exception:
                        pass
                return result

        return async_wrapper

    @functools.wraps(fn)
    def sync_wrapper(*args, **kwargs):
        attrs = _build_attrs(args, kwargs)
        with create_span(resolved_name, kind=kind, attributes=attrs or None) as span:
            result = fn(*args, **kwargs)
            if record_result:
                try:
                    span.set_attribute("result", str(result)[:200])
                except Exception:
                    pass
            return result

    return sync_wrapper
