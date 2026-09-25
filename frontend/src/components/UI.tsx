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

export function Brand() {
  return (
    <span
      data-ui="brand"
      className="inline-flex items-center gap-[9px] [font-weight:850] text-[30px] tracking-[-1.5px] leading-[1] mobile:text-[28px] mobile:gap-[8px]"
    >
      <span
        data-ui="brand-symbol"
        className="w-[38px] h-[38px] grid place-items-center [background:var(--blue)] text-[white] rounded-[12px] [transform:rotate(-5deg)] mobile:h-[35px] mobile:w-[35px] mobile:rounded-[11px] [&_svg]:[transform:rotate(5deg)] mobile:[&_svg]:w-[23px] mobile:[&_svg]:h-[23px]"
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
      whileTap={{ scale: 0.98 }}
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
      className={
        "flex items-center gap-[6px] justify-between [background:#eef2ff] text-[#4055a0] [border:1px_solid_#dbe3ff] rounded-[16px] py-[14px] px-[16px] text-[12px] leading-[1.7] mb-[18px] [overflow-wrap:anywhere] mobile:text-[11px] mobile:p-[12px] mobile:leading-[1.8] mobile:rounded-[13px] mobile:[[data-ui~=wizard-actions]_&]:mb-[12px] [[data-ui~=screen-loading]_[data-ui~=has-error]_&]:my-[12px] [[data-ui~=screen-loading]_[data-ui~=has-error]_&]:mx-0" +
        " " +
        (error
          ? "[[data-ui~=notice]&]:[background:#fff1ed] [[data-ui~=notice]&]:text-[#a34c37] [[data-ui~=notice]&]:[border-color:#f7dacf]"
          : "")
      }
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
      className={
        "relative flex items-center gap-[14px] [border:1.5px_solid_#e8ebf2] [background:#fff] rounded-[17px] text-left py-[18px] px-[15px] min-h-[83px] w-full [transition:border-color_0.18s,_background_0.18s] mobile:min-h-[89px] mobile:py-[17px] mobile:px-[14px] mobile:rounded-[17px] mobile:[background:#fff] [[data-ui~=group-grid]_&]:items-start [[data-ui~=group-grid]_&]:flex-col [[data-ui~=group-grid]_&]:gap-[14px] [[data-ui~=group-grid]_&]:py-[17px] [[data-ui~=group-grid]_&]:px-[15px] [[data-ui~=group-grid]_&]:min-h-[130px] mobile:[[data-ui~=group-grid]_&]:min-h-[141px] mobile:[[data-ui~=group-grid]_&]:py-[18px] mobile:[[data-ui~=group-grid]_&]:px-[14px] mobile-type:[[data-ui~=group-grid]_&]:min-h-[120px] short-mobile:[[data-ui~=group-grid]_&]:min-h-[104px] [[data-ui~=interests-grid]_&]:items-start [[data-ui~=interests-grid]_&]:flex-col [[data-ui~=interests-grid]_&]:py-[17px] [[data-ui~=interests-grid]_&]:px-[15px] [[data-ui~=interests-grid]_&]:min-h-[119px] [[data-ui~=interests-grid]_&]:gap-[8px] mobile:[[data-ui~=interests-grid]_&]:min-h-[118px] mobile:[[data-ui~=interests-grid]_&]:py-[16px] mobile:[[data-ui~=interests-grid]_&]:px-[13px] mobile-type:[[data-ui~=interests-grid]_&]:min-h-[120px] short-mobile:[[data-ui~=interests-grid]_&]:min-h-[104px] [[data-ui~=transport-choices]_&]:flex-col [[data-ui~=transport-choices]_&]:items-start [[data-ui~=transport-choices]_&]:py-[15px] [[data-ui~=transport-choices]_&]:px-[13px] [[data-ui~=transport-choices]_&]:min-h-[115px] [[data-ui~=transport-choices]_&]:gap-[7px] mobile:[[data-ui~=transport-choices]_&]:min-h-[120px] mobile:[[data-ui~=transport-choices]_&]:py-[16px] mobile:[[data-ui~=transport-choices]_&]:px-[14px]" +
        " " +
        (selected ? selectedChoiceStyles : "") +
        " " +
        className
      }
      onClick={onClick}
      whileTap={{ scale: 0.98 }}
    >
      {icon && (
        <span
          data-ui="choice-icon"
          className="text-[#9ba5b7] grid place-items-center h-[39px] w-[39px] shrink-0 [[data-ui~=choice][data-ui~=selected]_&]:text-brand [[data-ui~=group-grid]_&]:h-[34px] [[data-ui~=group-grid]_&]:w-[30px] [[data-ui~=interests-grid]_&]:h-[34px] [[data-ui~=interests-grid]_&]:w-[30px]"
        >
          {icon}
        </span>
      )}
      <span
        data-ui="choice-copy"
        className="[flex:1] min-w-0 [&_strong]:block [&_strong]:text-[12px] [&_strong]:[font-weight:750] mobile:[&_strong]:text-[12px] narrow:[&_strong]:text-[11px] mobile-type:[&_strong]:text-[13px] [&_small]:block [&_small]:text-[11px] [&_small]:font-medium [&_small]:text-[#959cab] [&_small]:mt-[5px] [&_small]:leading-[1.5] mobile:[&_small]:text-[11px] narrow:[&_small]:text-[11px] mobile-type:[&_small]:text-[12px] mobile-type:[&_small]:leading-[1.6] [[data-ui~=group-grid]_&_strong]:text-[11px] mobile:[[data-ui~=group-grid]_&_strong]:text-[11px] narrow:[[data-ui~=group-grid]_&_strong]:text-[11px] mobile-type:[[data-ui~=group-grid]_&_strong]:text-[13px] [[data-ui~=interests-grid]_&_strong]:text-[11px] mobile:[[data-ui~=interests-grid]_&_strong]:text-[11px] narrow:[[data-ui~=interests-grid]_&_strong]:text-[11px] mobile-type:[[data-ui~=interests-grid]_&_strong]:text-[13px] [[data-ui~=interests-grid]_&_small]:text-[11px] mobile:[[data-ui~=interests-grid]_&_small]:text-[11px] [[data-ui~=transport-choices]_&_strong]:text-[11px] mobile:[[data-ui~=transport-choices]_&_strong]:text-[12px] [[data-ui~=transport-choices]_&_small]:text-[11px] mobile:[[data-ui~=transport-choices]_&_small]:text-[11px] mobile:[[data-ui~=group-grid]_&_small]:text-[11px] narrow:[[data-ui~=group-grid]_&_small]:text-[11px] mobile-type:[[data-ui~=group-grid]_&_small]:text-[12px]"
      >
        <strong>{title}</strong>
        {subtitle && <small>{subtitle}</small>}
      </span>
      <span
        data-ui="choice-check"
        className={
          "w-[18px] h-[18px] shrink-0 [border:1.5px_solid_#e0e4ec] rounded-[50%] grid place-items-center [background:#fff] [[data-ui~=selected]_>_&]:[border-color:var(--blue)] [[data-ui~=selected]_>_&]:[background:var(--blue)] [[data-ui~=selected]_>_&]:text-[#fff] [[data-ui~=group-grid]_&]:absolute [[data-ui~=group-grid]_&]:right-[13px] [[data-ui~=group-grid]_&]:top-[14px] [[data-ui~=interests-grid]_&]:absolute [[data-ui~=interests-grid]_&]:right-[13px] [[data-ui~=interests-grid]_&]:top-[14px] [[data-ui~=transport-choices]_&]:absolute [[data-ui~=transport-choices]_&]:right-[11px] [[data-ui~=transport-choices]_&]:top-[12px]"
        }
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
      className="flex items-center gap-[13px] [&_button]:[border:1px_solid_#e7ebf3] [&_button]:grid [&_button]:place-items-center [&_button]:min-h-[40px] [&_button]:h-[40px] [&_button]:w-[40px] [&_button]:rounded-[12px] [&_button]:[background:#fff] [&_button]:text-brand mobile:[&_button]:h-[44px] mobile:[&_button]:min-h-[44px] mobile:[&_button]:w-[44px] mobile:[&_button]:[background:white] [&_button:disabled]:text-[#aeb5c5] [&_button:disabled]:[cursor:default] [&_output]:text-[20px] [&_output]:[font-weight:750] [&_output]:min-w-[22px] [&_output]:text-center"
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
