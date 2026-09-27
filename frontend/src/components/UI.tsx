import {
  iconButtonStyles,
  primaryButtonStyles,
  selectedChoiceStyles,
} from "../ui-styles";
import type { ReactNode } from "react";
import {
  ArrowRight,
  Check,
  Compass,
  LoaderCircle,
  Minus,
  Plus,
  X,
} from "lucide-react";
import { motion } from "motion/react";


const noticeStyles = `
  flex items-center gap-1.5 justify-between bg-[#eef2ff] text-[#4055a0] [border:1px_solid_#dbe3ff]
  rounded-2xl py-3.5 px-4 text-[12px] leading-[1.7] mb-4.5 wrap-anywhere mobile:text-[11px] mobile:p-3
  mobile:leading-[1.8] mobile:rounded-[13px] mobile:[[data-ui~=wizard-actions]_&]:mb-3
  [[data-ui~=screen-loading]_[data-ui~=has-error]_&]:my-3
  [[data-ui~=screen-loading]_[data-ui~=has-error]_&]:mx-0
`;

const choiceStyles = `
  relative flex items-center gap-3.5 [border:1.5px_solid_#e8ebf2] bg-white rounded-[17px] text-left
  py-4.5 px-[15px] min-h-[83px] w-full [transition:border-color_0.18s,_background_0.18s]
  mobile:min-h-[89px] mobile:py-[17px] mobile:px-3.5 mobile:rounded-[17px] mobile:bg-white
  [[data-ui~=group-grid]_&]:items-start [[data-ui~=group-grid]_&]:flex-col
  [[data-ui~=group-grid]_&]:gap-3.5 [[data-ui~=group-grid]_&]:py-[17px]
  [[data-ui~=group-grid]_&]:px-[15px] [[data-ui~=group-grid]_&]:min-h-32.5
  mobile:[[data-ui~=group-grid]_&]:min-h-[141px] mobile:[[data-ui~=group-grid]_&]:py-4.5
  mobile:[[data-ui~=group-grid]_&]:px-3.5 mobile-type:[[data-ui~=group-grid]_&]:min-h-30
  short-mobile:[[data-ui~=group-grid]_&]:min-h-26 [[data-ui~=interests-grid]_&]:items-start
  [[data-ui~=interests-grid]_&]:flex-col [[data-ui~=interests-grid]_&]:py-[17px]
  [[data-ui~=interests-grid]_&]:px-[15px] [[data-ui~=interests-grid]_&]:min-h-[119px]
  [[data-ui~=interests-grid]_&]:gap-2 mobile:[[data-ui~=interests-grid]_&]:min-h-29.5
  mobile:[[data-ui~=interests-grid]_&]:py-4 mobile:[[data-ui~=interests-grid]_&]:px-[13px]
  mobile-type:[[data-ui~=interests-grid]_&]:min-h-30
  short-mobile:[[data-ui~=interests-grid]_&]:min-h-26 [[data-ui~=transport-choices]_&]:flex-col
  [[data-ui~=transport-choices]_&]:items-start [[data-ui~=transport-choices]_&]:py-[15px]
  [[data-ui~=transport-choices]_&]:px-[13px] [[data-ui~=transport-choices]_&]:min-h-[115px]
  [[data-ui~=transport-choices]_&]:gap-[7px] mobile:[[data-ui~=transport-choices]_&]:min-h-30
  mobile:[[data-ui~=transport-choices]_&]:py-4 mobile:[[data-ui~=transport-choices]_&]:px-3.5
`;

export function Brand() {
  return (
    <span
      data-ui="brand"
      className="inline-flex items-center gap-[9px] font-[850] text-[30px] tracking-[-1.5px] leading-none
        mobile:text-[28px] mobile:gap-2"
    >
      <span
        data-ui="brand-symbol"
        className="size-9.5 grid place-items-center bg-brand text-white rounded-xl [transform:rotate(-5deg)]
          mobile:size-[35px] mobile:rounded-[11px] [&_svg]:[transform:rotate(5deg)]
          mobile:[&_svg]:size-[23px]"
      >
        <Compass size={25} strokeWidth={1.8} />
      </span>
      <span>
        рядом
        <span data-ui="brand-period" className="text-brand">
          .
        </span>
      </span>
    </span>
  );
}
export function Primary({
  children,
  onClick,
  busy,
  disabled,
  type = "button",
  id,
  arrow = true,
}: {
  children: ReactNode;
  onClick?: () => void;
  busy?: boolean;
  disabled?: boolean;
  type?: "button" | "submit";
  id?: string;
  arrow?: boolean;
}) {
  return (
    <motion.button
      id={id}
      type={type}
      data-ui="button primary"
      className={primaryButtonStyles}
      onClick={onClick}
      disabled={disabled || busy}
      whileTap={{ opacity: 0.8 }}
    >
      <span>{children}</span>
      {busy ? (
        <LoaderCircle
          data-ui="spin"
          className="[animation:spin_1s_linear_infinite]"
          size={20}
        />
      ) : arrow ? (
        <ArrowRight size={20} />
      ) : null}
    </motion.button>
  );
}
export function Notice({
  children,
  error = false,
  onClose,
}: {
  children: ReactNode;
  error?: boolean;
  onClose?: () => void;
}) {
  return (
    <div
      data-ui={`notice ${error ? "error" : ""}`}
      className={`${noticeStyles} ${
        error
          ? "[[data-ui~=notice]&]:bg-[#fff1ed] [[data-ui~=notice]&]:text-[#a34c37] [[data-ui~=notice]&]:border-[#f7dacf]"
          : ""
      }`}
      role={error ? "alert" : "status"}
    >
      <span>{children}</span>
      {onClose && (
        <button
          data-ui="icon-button"
          className={iconButtonStyles}
          aria-label="Закрыть сообщение"
          onClick={onClose}
        >
          <X size={18} />
        </button>
      )}
    </div>
  );
}
export function Choice({
  selected,
  onClick,
  icon,
  title,
  subtitle,
  className = "",
}: {
  selected: boolean;
  onClick: () => void;
  icon?: ReactNode;
  title: string;
  subtitle?: string;
  className?: string;
}) {
  return (
    <motion.button
      type="button"
      aria-pressed={selected}
      data-ui={`choice ${selected ? "selected" : ""}`}
      className={`${choiceStyles} ${selected ? selectedChoiceStyles : ""} ${className}`}
      onClick={onClick}
      whileTap={{ opacity: 0.8 }}
    >
      {icon && (
        <span
          data-ui="choice-icon"
          className="text-[#9ba5b7] grid place-items-center size-[39px] shrink-0
            [[data-ui~=choice][data-ui~=selected]_&]:text-brand [[data-ui~=group-grid]_&]:h-8.5
            [[data-ui~=group-grid]_&]:w-7.5 [[data-ui~=interests-grid]_&]:h-8.5
            [[data-ui~=interests-grid]_&]:w-7.5"
        >
          {icon}
        </span>
      )}
      <span
        data-ui="choice-copy"
        className="flex-1 min-w-0 [&_strong]:block [&_strong]:text-[12px] [&_strong]:font-[750]
          mobile:[&_strong]:text-[12px] narrow:[&_strong]:text-[11px]
          mobile-type:[&_strong]:text-[13px] [&_small]:block [&_small]:text-[11px]
          [&_small]:font-medium [&_small]:text-[#959cab] [&_small]:mt-[5px] [&_small]:leading-[1.5]
          mobile:[&_small]:text-[11px] narrow:[&_small]:text-[11px] mobile-type:[&_small]:text-[12px]
          mobile-type:[&_small]:leading-[1.6] [[data-ui~=group-grid]_&_strong]:text-[11px]
          mobile:[[data-ui~=group-grid]_&_strong]:text-[11px]
          narrow:[[data-ui~=group-grid]_&_strong]:text-[11px]
          mobile-type:[[data-ui~=group-grid]_&_strong]:text-[13px]
          [[data-ui~=interests-grid]_&_strong]:text-[11px]
          mobile:[[data-ui~=interests-grid]_&_strong]:text-[11px]
          narrow:[[data-ui~=interests-grid]_&_strong]:text-[11px]
          mobile-type:[[data-ui~=interests-grid]_&_strong]:text-[13px]
          [[data-ui~=interests-grid]_&_small]:text-[11px]
          mobile:[[data-ui~=interests-grid]_&_small]:text-[11px]
          [[data-ui~=transport-choices]_&_strong]:text-[11px]
          mobile:[[data-ui~=transport-choices]_&_strong]:text-[12px]
          [[data-ui~=transport-choices]_&_small]:text-[11px]
          mobile:[[data-ui~=transport-choices]_&_small]:text-[11px]
          mobile:[[data-ui~=group-grid]_&_small]:text-[11px]
          narrow:[[data-ui~=group-grid]_&_small]:text-[11px]
          mobile-type:[[data-ui~=group-grid]_&_small]:text-[12px]"
      >
        <strong>{title}</strong>
        {subtitle && <small>{subtitle}</small>}
      </span>
      <span
        data-ui="choice-check"
        className="size-4.5 shrink-0 [border:1.5px_solid_#e0e4ec] rounded-[50%] grid place-items-center
          bg-white [[data-ui~=selected]_>_&]:border-brand [[data-ui~=selected]_>_&]:bg-brand
          [[data-ui~=selected]_>_&]:text-white [[data-ui~=group-grid]_&]:absolute
          [[data-ui~=group-grid]_&]:right-[13px] [[data-ui~=group-grid]_&]:top-3.5
          [[data-ui~=interests-grid]_&]:absolute [[data-ui~=interests-grid]_&]:right-[13px]
          [[data-ui~=interests-grid]_&]:top-3.5 [[data-ui~=transport-choices]_&]:absolute
          [[data-ui~=transport-choices]_&]:right-[11px] [[data-ui~=transport-choices]_&]:top-3"
      >
        {selected && <Check size={13} strokeWidth={3} />}
      </span>
    </motion.button>
  );
}
export function Counter({
  value,
  onChange,
  label,
  min = 1,
  max = 20,
}: {
  value: number;
  onChange: (value: number) => void;
  label: string;
  min?: number;
  max?: number;
}) {
  return (
    <div
      data-ui="counter"
      className="flex items-center gap-[13px] [&_button]:[border:1px_solid_#e7ebf3] [&_button]:grid
        [&_button]:place-items-center [&_button]:min-h-10 [&_button]:size-10 [&_button]:rounded-xl
        [&_button]:bg-white [&_button]:text-brand mobile:[&_button]:min-h-11 mobile:[&_button]:size-11
        mobile:[&_button]:bg-white [&_button:disabled]:text-[#aeb5c5]
        [&_button:disabled]:cursor-default [&_output]:text-[20px] [&_output]:font-[750]
        [&_output]:min-w-5.5 [&_output]:text-center"
    >
      <button
        type="button"
        aria-label={`Уменьшить: ${label}`}
        disabled={value <= min}
        onClick={() => onChange(value - 1)}
      >
        <Minus size={20} />
      </button>
      <output aria-label={label}>{value}</output>
      <button
        type="button"
        aria-label={`Увеличить: ${label}`}
        disabled={value >= max}
        onClick={() => onChange(value + 1)}
      >
        <Plus size={20} />
      </button>
    </div>
  );
}
