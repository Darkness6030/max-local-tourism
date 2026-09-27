/** Shared Tailwind recipes for repeated primitives and interactive states. */

export const appHeaderStyles = [
  "max-w-280 h-25 m-auto flex items-center justify-between",
  "[border-bottom:1px_solid_var(--line)] desktop-fit:mx-[35px] mobile:h-19 mobile:my-0",
  "mobile:mx-5.5 mobile:[border:0] mobile:pt-[env(safe-area-inset-top)] narrow:my-0 narrow:mx-[17px]",
  "mobile-spacing:mx-6 narrow-spacing:mx-5 short:h-16 short:min-h-16 short:shrink-0",
  "mobile:[[data-ui~=screen-wizard]_&]:hidden mobile:[[data-ui~=screen-result]_&]:hidden",
  "[[data-ui~=screen-preset]_&]:hidden [[data-ui~=screen-loading]_&]:w-[calc(100%_-_48px)]",
  "[[data-ui~=screen-loading]_&]:my-0 [[data-ui~=screen-loading]_&]:mx-auto",
  "[[data-ui~=screen-loading]_&]:shrink-0",
  "loading-narrow:[[data-ui~=screen-loading]_&]:w-[calc(100%_-_40px)]",
].join(" ");

export const appMainStyles = [
  "max-w-280 m-auto py-6 px-0 desktop-fit:mx-[35px] mobile:m-0 mobile:pt-4",
  "mobile:px-6 mobile:pb-6 narrow:px-[17px] narrow-spacing:px-5 short:pt-4",
  "mobile:[[data-ui~=screen-wizard]_&]:p-0 narrow-spacing:[[data-ui~=screen-wizard]_&]:p-0",
  "mobile:[[data-ui~=screen-result]_&]:pt-0 mobile:[[data-ui~=screen-result]_&]:px-6",
  "mobile:[[data-ui~=screen-result]_&]:pb-[calc(92px_+_env(safe-area-inset-bottom))]",
  "narrow:[[data-ui~=screen-result]_&]:px-[17px] desktop-result:[[data-ui~=screen-result]_&]:pb-26",
  "narrow-spacing:[[data-ui~=screen-result]_&]:px-5 [[data-ui~=screen-preset]_&]:pt-0",
  "[[data-ui~=screen-preset]_&]:pb-[calc(136px_+_env(safe-area-inset-bottom))]",
  "preset-mobile:[[data-ui~=screen-preset]_&]:pb-[calc(110px_+_env(safe-area-inset-bottom))]",
  "[[data-ui~=screen-loading]_&]:flex-1 [[data-ui~=screen-loading]_&]:flex",
  "[[data-ui~=screen-loading]_&]:items-center [[data-ui~=screen-loading]_&]:w-full",
  "[[data-ui~=screen-loading]_&]:my-0 [[data-ui~=screen-loading]_&]:mx-auto",
  "[[data-ui~=screen-loading]_&]:pt-2",
  "[[data-ui~=screen-loading]_&]:pb-[max(12px,_env(safe-area-inset-bottom))]",
].join(" ");

export const emptyStateStyles = [
  "flex flex-col items-center justify-center py-[45px] px-5 text-center max-w-122.5 m-auto",
  "min-h-92.5 mobile:min-h-97.5 mobile:py-7.5 mobile:px-2.5 [&_h1]:text-[28px]",
  "[&_h1]:tracking-[-1px] [&_h1]:mt-5 [&_h1]:mx-0 [&_h1]:mb-2.5 [&_h2]:text-[22px]",
  "[&_h2]:font-[750] [&_h2]:tracking-[-0.7px] mobile:[&_h2]:text-[21px] [&_p]:text-[#959eb1]",
  "[&_p]:text-[12px] [&_p]:leading-[1.9] [&_p]:mt-3.5 [&_p]:mx-0 [&_p]:mb-[25px] [&_p]:max-w-80",
  "mobile:[&_p]:text-[11px] mobile:[&_p]:max-w-70 mobile-type:[&_p]:text-[14px]",
  "[[data-ui~=trips-page]_&]:min-h-0 [[data-ui~=trips-page]_&]:pt-3",
  "[[data-ui~=trips-page]_&]:px-2 [[data-ui~=trips-page]_&]:pb-4",
  "[[data-ui~=trips-page]_&_p]:mt-3 [[data-ui~=trips-page]_&_p]:mx-0",
  "[[data-ui~=trips-page]_&_p]:mb-5 [[data-ui~=trips-page]_&_p]:leading-[1.7]",
].join(" ");

export const textButtonStyles = [
  "inline-flex items-center justify-center gap-2 text-[12px] font-[650]",
  "bg-transparent text-brand py-2.5 px-1 [[data-ui~=onboarding-header]_&]:text-[12px]",
  "mobile:[[data-ui~=onboarding-header]_&]:text-[11px] [[data-ui~=result-hero]_>_&]:text-[11px]",
  "[[data-ui~=result-hero]_>_&]:min-h-9.5 mobile:[[data-ui~=result-hero]_>_&]:text-[11px]",
  "[[data-ui~=train-bottom]_>_&]:text-[11px]",
  "mobile:[[data-ui~=train-bottom]_>_&]:text-[11px]",
  "mobile-type:[[data-ui~=train-bottom]_>_&]:text-[12px]",
].join(" ");

export const avatarStyles = [
  "size-10 min-h-10 bg-[#e9edff] text-brand [border:1px_solid_#dce2ff] grid",
  "place-items-center rounded-[50%] font-bold p-0 shrink-0 mobile:size-9",
  "mobile:min-h-9 overflow-hidden [&_>_img]:size-full [&_>_img]:object-cover",
  "[&_>_img]:rounded-[inherit]",
].join(" ");

export const eyebrowStyles = [
  "block text-[11px] font-extrabold tracking-[1.4px] text-muted mobile:text-[11px]",
  "mobile:tracking-[1.05px] mobile-type:text-[10px] [[data-ui~=onboarding-copy]_&]:text-[11px]",
  "[[data-ui~=onboarding-copy]_&]:text-brand [[data-ui~=onboarding-copy]_&]:tracking-[1.8px]",
  "mobile:[[data-ui~=onboarding-copy]_&]:text-[11px]",
  "mobile:[[data-ui~=onboarding-copy]_&]:tracking-[1.5px] [[data-ui~=step-heading]_&]:text-[11px]",
  "[[data-ui~=step-heading]_&]:tracking-[1.5px] [[data-ui~=step-heading]_&]:text-[#a2a7b7]",
  "mobile:[[data-ui~=step-heading]_&]:text-[11px] [[data-ui~=loading-page]_&]:text-[11px]",
  "[[data-ui~=loading-page]_&]:tracking-[1.4px] [[data-ui~=loading-page]_&]:text-[#8b95ae]",
  "[[data-ui~=budget-panel]_>_&]:text-[11px] [[data-ui~=budget-panel]_>_&]:tracking-[1px]",
  "mobile:[[data-ui~=budget-panel]_>_&]:text-[11px] mobile:[[data-ui~=loading-page]_>_&]:text-[11px]",
  "mobile:[[data-ui~=loading-page]_>_&]:tracking-[1.2px] narrow:[[data-ui~=home-heading]_&]:text-[11px]",
  "[[data-ui~=preset-section]_&]:text-brand [[data-ui~=preset-section]_&]:mb-2",
  "[[data-ui~=preset-section]_&]:text-[10px] [[data-ui~=preset-intro]_&]:text-brand",
  "[[data-ui~=preset-intro]_&]:tracking-[0.6px]",
].join(" ");

export const sectionHeadingStyles = [
  "flex justify-between items-baseline mb-[17px] gap-2.5 mobile:mb-3.5 mobile-type:items-start",
  "mobile-type:gap-2.5 [&_h2]:text-[18px] [&_h2]:tracking-[-0.55px] [&_h2]:font-extrabold",
  "mobile:[&_h2]:text-[15px] mobile:[&_h2]:tracking-[-0.5px] narrow:[&_h2]:text-[13px]",
  "[&_>_span]:text-[11px] [&_>_span]:text-muted mobile:[&_>_span]:text-[11px] mobile:[&_>_span]:m-0",
  "narrow:[&_>_span]:text-[11px] mobile-type:[&_>_span]:max-w-25 mobile-type:[&_>_span]:text-right",
  "mobile-type:[&_>_span]:leading-[1.6] [[data-ui~=home-side]_&]:flex [[data-ui~=home-side]_&]:flex-wrap",
  "[[data-ui~=home-side]_&]:gap-[4px_12px] [[data-ui~=home-side]_&]:items-baseline",
  "[[data-ui~=home-side]_&_>_span]:block [[data-ui~=home-side]_&_>_span]:mt-[5px]",
  "mobile:[[data-ui~=home-side]_&_>_span]:text-[11px] mobile:[[data-ui~=home-side]_&_>_span]:m-0",
  "narrow:[[data-ui~=home-side]_&_>_span]:text-[11px] [[data-ui~=home-side]_&_>_span]:max-w-none",
  "[[data-ui~=home-side]_&_>_span]:shrink-0 [[data-ui~=home-side]_&_>_span]:whitespace-nowrap",
  "[[data-ui~=home-side]_&_>_span]:text-left mobile:[[data-ui~=example-section]_>_&]:block",
  "mobile:[[data-ui~=example-section]_>_&_>_span]:block",
  "mobile:[[data-ui~=example-section]_>_&_>_span]:mt-1.5",
  "mobile-type:[[data-ui~=example-section]_&_>_span]:max-w-none",
  "mobile-type:[[data-ui~=example-section]_&_>_span]:text-left",
  "[[data-ui~=preset-section]_&]:[align-items:end] preset-mobile:[[data-ui~=preset-section]_&]:flex-wrap",
  "preset-mobile:[[data-ui~=preset-section]_&]:gap-2 [[data-ui~=preset-section]_&_h2]:text-[23px]",
  "[[data-ui~=preset-section]_&_h2]:tracking-[-0.8px]",
  "preset-mobile:[[data-ui~=preset-section]_&_h2]:text-[20px]",
  "preset-mobile:[[data-ui~=preset-section]_&_>_span]:max-w-none",
  "preset-mobile:[[data-ui~=preset-section]_&_>_span]:text-left",
].join(" ");

export const tripsPageStyles = [
  "max-w-172.5 my-3 mx-auto mobile:my-0.5 mobile:mx-0 [&_>_h1]:text-[37px]",
  "[&_>_h1]:leading-[1.3] [&_>_h1]:tracking-[-1.4px] [&_>_h1]:font-extrabold [&_>_h1]:mt-3.5",
  "[&_>_h1]:mx-0 mobile:[&_>_h1]:text-[29px] mobile:[&_>_h1]:tracking-[-1.1px]",
  "mobile:[&_>_h1]:mt-3 mobile:[&_>_h1]:mx-0",
].join(" ");

export const activeStyles = [
  "[[data-ui~=bottom-nav]_button&]:text-brand",
  "[[data-ui~=wizard-aside]_li&]:text-ink",
  "[[data-ui~=wizard-aside]_li&]:font-[750]",
  "[[data-ui~=wizard-aside]_li&_>_span]:bg-brand",
  "[[data-ui~=wizard-aside]_li&_>_span]:text-white",
  "[[data-ui~=wizard-aside]_li&_>_span]:border-brand",
  "[[data-ui~=step-progress]_>_span&]:bg-brand",
  "[[data-ui~=quick-chips]_button&]:border-[#cdd6ff]",
  "[[data-ui~=quick-chips]_button&]:bg-[#f0f3ff] [[data-ui~=quick-chips]_button&]:text-brand",
  "[[data-ui~=segmented]_button&]:bg-white [[data-ui~=segmented]_button&]:text-brand",
  "[[data-ui~=segmented]_button&]:[box-shadow:0_2px_5px_#26335308]",
  "[[data-ui~=segmented]_button&]:font-[750] [[data-ui~=result-tabs]_>_button&]:text-brand",
  "[[data-ui~=result-tabs]_>_button&]:font-[750]",
  "[[data-ui~=day-selector]_>_button&]:bg-[#eaf0ff]",
  "[[data-ui~=day-selector]_>_button&]:border-[#aabaf6]",
  "[[data-ui~=day-selector]_>_button&]:text-brand",
].join(" ");

export const doneStyles = [
  "[[data-ui~=wizard-aside]_li&]:text-[#607ec7]",
  "[[data-ui~=wizard-aside]_li&_>_span]:bg-[#e9edff]",
  "[[data-ui~=wizard-aside]_li&_>_span]:border-[#e0e6ff]",
  "[[data-ui~=wizard-aside]_li&_>_span]:text-brand [[data-ui~=generation-stages]_>_span&]:text-[#6677b6]",
].join(" ");

export const iconButtonStyles = [
  "size-11 min-h-11 rounded-[50%] inline-grid place-items-center bg-transparent",
  "text-ink shrink-0 [&:hover]:bg-[#edeff6] [[data-ui~=notice]_&]:w-8",
  "[[data-ui~=notice]_&]:min-h-8 [[data-ui~=notice]_&]:h-8",
  "mobile:[[data-ui~=wizard-top]_&]:bg-white",
  "mobile:[[data-ui~=wizard-top]_&]:[border:1px_solid_#edf0f6] mobile:[[data-ui~=wizard-top]_&]:w-[39px]",
  "mobile:[[data-ui~=wizard-top]_&]:h-[39px] mobile:[[data-ui~=wizard-top]_&]:min-h-[39px]",
].join(" ");

export const presetInfoCardStyles = [
  "p-5.5 bg-white [border:1px_solid_var(--line)] rounded-[22px] [&_>_h2]:text-[17px]",
  "[&_>_h2]:mt-4 [&_>_h2]:mx-0 [&_>_h2]:mb-3 [&_>_h2]:tracking-[-0.3px] [&_p]:text-[12px]",
  "[&_p]:leading-[1.8] [&_p]:text-[#687389] [&_small]:text-[12px] [&_small]:leading-[1.8]",
  "[&_small]:text-[#687389] [&_dl]:my-4 [&_dl]:mx-0 [&_dl]:py-3 [&_dl]:px-0",
  "[&_dl]:[border-block:1px_solid_var(--line)] [&_dl_>_div]:flex [&_dl_>_div]:justify-between",
  "[&_dl_>_div]:gap-3 [&_dl_>_div]:py-[7px] [&_dl_>_div]:px-0 [&_dl_>_div]:text-[12px]",
  "[&_dl_>_div]:leading-[1.5] [&_dd]:m-0 [&_dd]:whitespace-nowrap [&_dd]:font-[750]",
].join(" ");

export const packingListStyles = [
  "grid grid-cols-[1fr_1fr] gap-[5px_10px] mt-2 mobile:gap-[4px_9px] mobile-type:grid-cols-[1fr]",
  "[&_label]:relative [&_label]:flex [&_label]:gap-2 [&_label]:items-center [&_label]:text-[11px]",
  "[&_label]:leading-[1.6] [&_label]:text-[#8e96a8] [&_label]:min-h-9 [&_label]:cursor-pointer",
  "mobile:[&_label]:text-[11px] mobile:[&_label]:min-h-10 mobile-type:[&_label]:text-[12px]",
  "mobile-type:[&_label]:min-h-11 [&_input]:absolute [&_input]:opacity-0 [&_input]:w-5",
  "[&_input]:h-5 [&_input]:min-h-0 [&_input]:m-0 [[data-ui~=preset-info-card]_&]:flex",
  "[[data-ui~=preset-info-card]_&]:flex-col",
  "[[data-ui~=preset-info-card][data-ui~=preset-packing-card]_&]:mt-1.5",
].join(" ");

export const packingCheckboxStyles = [
  "size-4.5 [border:1px_solid_#dfe4ef] rounded-md grid place-items-center shrink-0",
  "[[data-ui~=packed]_>_&]:bg-brand [[data-ui~=packed]_>_&]:border-brand",
  "[[data-ui~=packed]_>_&]:text-white",
  "[[data-ui~=packing-list]_input:focus-visible_+_&]:[outline:3px_solid_#a3b1ff]",
  "[[data-ui~=packing-list]_input:focus-visible_+_&]:outline-offset-3",
].join(" ");

const fieldStyles = [
  "block text-[11px] font-[750] leading-[1.6] mobile:text-[11px] mobile-type:text-[13px]",
  "[&_input]:mt-[9px] [&_input]:block [&_input]:w-full [&_input]:[border:1px_solid_#e6e9f0]",
  "[&_input]:bg-[#fafbfe] [&_input]:rounded-[13px] [&_input]:p-3.5 [&_input]:text-[13px]",
  "[&_input]:text-ink [&_input]:min-h-[51px] mobile:[&_input]:text-[16px] mobile:[&_input]:min-h-13.5",
  "mobile:[&_input]:bg-white mobile:[&_input]:p-3.5 [&_textarea]:mt-[9px] [&_textarea]:block",
  "[&_textarea]:w-full [&_textarea]:[border:1px_solid_#e6e9f0] [&_textarea]:bg-[#fafbfe]",
  "[&_textarea]:rounded-[13px] [&_textarea]:p-3.5 [&_textarea]:text-[13px] [&_textarea]:text-ink",
  "[&_textarea]:resize-y [&_textarea]:min-h-23 [&_textarea]:leading-[1.7]",
  "mobile:[&_textarea]:bg-white mobile:[&_textarea]:p-3.5 mobile:[&_textarea]:text-[16px]",
  "mobile:[&_textarea]:min-h-25 [&_select]:mt-[9px] [&_select]:block [&_select]:w-full",
  "[&_select]:[border:1px_solid_#e6e9f0] [&_select]:[background:#fafbfe] [&_select]:rounded-[13px]",
  "[&_select]:p-3.5 [&_select]:text-[13px] [&_select]:text-ink [&_select]:min-h-[51px]",
  "mobile:[&_select]:min-h-13.5 mobile:[&_select]:[background:#fff]",
  "mobile:[&_select]:p-3.5 [&_input::placeholder]:text-[#a3a9b8] [&_input::placeholder]:text-[12px]",
  "mobile:[&_input::placeholder]:text-[12px] [&_textarea::placeholder]:text-[#a3a9b8]",
  "[&_textarea::placeholder]:text-[12px] mobile:[&_textarea::placeholder]:text-[12px]",
  "[[data-ui~=fields-pair]_&]:text-[11px] mobile:[[data-ui~=fields-pair]_&]:text-[11px]",
].join(" ");

export const fieldLabelStyles = `${fieldStyles} mobile:[&_select]:text-[16px]`;

export const inlineNoteStyles = [
  "flex gap-2.5 items-start text-[11px] leading-[1.8] text-[#929bae] bg-[#f8f9fc]",
  "rounded-xl p-[13px] mt-4 mobile:text-[11px] mobile:bg-[#f0f3fa] mobile:mt-4",
  "mobile:p-[13px] mobile-type:text-[12px] [&_>_svg]:mt-0.5 [&_>_svg]:text-[#8993b0]",
  "mobile:[[data-ui~=budget-panel]_&]:text-[11px] mobile-type:[[data-ui~=budget-panel]_&]:text-[12px]",
].join(" ");

export const inputWithIconStyles = [
  "[&_input]:block [&_input]:w-full [&_input]:[border:1px_solid_#e6e9f0] [&_input]:bg-[#fafbfe]",
  "[&_input]:rounded-[13px] [&_input]:py-3.5 [&_input]:pr-3.5 [&_input]:text-[13px]",
  "[&_input]:text-ink [&_input]:min-h-[51px] [&_input]:pl-11 mobile:[&_input]:text-[16px]",
  "mobile:[&_input]:min-h-13.5 mobile:[&_input]:bg-white mobile:[&_input]:py-3.5",
  "mobile:[&_input]:pr-3.5 mobile:[&_input]:pl-11 [&_select]:block [&_select]:w-full",
  "[&_select]:[border:1px_solid_#e6e9f0] [&_select]:[background:#fafbfe] [&_select]:rounded-[13px]",
  "[&_select]:py-0 [&_select]:h-13.5 [&_select]:leading-[20px] [&_select]:pr-3.5 [&_select]:text-[13px] [&_select]:text-ink",
  "[&_select]:min-h-[51px] [&_select]:pl-11 [&_select]:appearance-none",
  "[&_select]:[background-image:url(\"data:image/svg+xml,%3Csvg_xmlns='http://www.w3.org/2000/svg'_width='12'_height='12'_viewBox='0_0_24_24'_fill='none'_stroke='%237c8293'_stroke-width='2'%3E%3Cpath_d='m6_9_6_6_6-6'/%3E%3C/svg%3E\")]",
  "[&_select]:[background-repeat:no-repeat] [&_select]:[background-position:calc(100%_-_18px)_center]",
  "mobile:[&_select]:text-[16px] mobile:[&_select]:min-h-13.5 mobile:[&_select]:[background:#fff]",
  "mobile:[&_select]:py-0 [&_select]:h-13.5 [&_select]:leading-[20px] mobile:[&_select]:pr-3.5 mobile:[&_select]:pl-11 flex items-center",
  "relative mt-[9px] [&_>_svg]:absolute [&_>_svg]:left-[15px] [&_>_svg]:text-[#7b88b4]",
  "[&_>_svg]:pointer-events-none",
].join(" ");

const softIconStyles = [
  "size-[47px] grid place-items-center rounded-[15px] shrink-0 tablet:[[data-ui~=how-card]_&]:h-[37px]",
  "tablet:[[data-ui~=how-card]_&]:w-[37px] tablet:[[data-ui~=how-card]_&]:rounded-xl",
  "mobile:[[data-ui~=how-card]_&]:size-9.5",
  "mobile:[[data-ui~=how-card]_&]:rounded-xl mobile:[[data-ui~=section-title]_&]:h-[39px]",
  "mobile:[[data-ui~=section-title]_&]:w-[39px] mobile:[[data-ui~=section-title]_&]:rounded-[13px]",
  "mobile:[[data-ui~=map-button]_&]:size-[37px]",
  "mobile:[[data-ui~=map-button]_&]:rounded-xl mobile:[[data-ui~=saved-trip]_>_&]:h-9.5",
  "mobile:[[data-ui~=saved-trip]_>_&]:w-9.5 mobile:[[data-ui~=saved-trip]_>_&]:rounded-xl",
  "mobile:[[data-ui~=about-info]_&]:size-[37px]",
  "mobile:[[data-ui~=about-info]_&]:rounded-xl",
].join(" ");

export const softBlueIconStyles = `${softIconStyles} [[data-ui~=soft-icon]&]:bg-[#ecf0ff] [[data-ui~=soft-icon]&]:text-brand`;

export const primaryButtonStyles = [
  "min-h-13.5 inline-flex items-center justify-center gap-3 py-[15px] px-5.5 rounded-[17px] text-[14px]",
  "font-[750] no-underline [transition:background_0.18s,_box-shadow_0.18s] mobile:min-h-[53px]",
  "mobile:text-[13px] mobile:rounded-[15px] mobile-type:text-[14px] [[data-ui~=button]&]:bg-brand",
  "[[data-ui~=button]&]:text-white [[data-ui~=button]&]:[box-shadow:0_6px_14px_#3d5af420]",
  "[[data-ui~=button]&:hover:not(:disabled)]:[background:var(--blue-dark)]",
  "[[data-ui~=button]&:hover:not(:disabled)]:[box-shadow:0_8px_18px_#3d5af42c]",
  "[[data-ui~=button]&_>_span:first-child]:flex-1 [[data-ui~=button]&_>_span:first-child]:text-left",
  "[[data-ui~=onboarding-controls]_&]:w-full [[data-ui~=adventure-copy]_[data-ui~=button]&]:w-full",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&]:bg-white",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&]:text-ink",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&]:[box-shadow:0_5px_10px_#1423380d]",
  "mobile:[[data-ui~=adventure-copy]_[data-ui~=button]&]:text-[12px]",
  "mobile:[[data-ui~=adventure-copy]_[data-ui~=button]&]:min-h-12.5",
  "mobile:[[data-ui~=adventure-copy]_[data-ui~=button]&]:rounded-[14px]",
  "mobile:[[data-ui~=adventure-copy]_[data-ui~=button]&]:py-[13px]",
  "mobile:[[data-ui~=adventure-copy]_[data-ui~=button]&]:px-[17px]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:hover:not(:disabled)]:bg-[#eef2ff]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:hover:not(:disabled)]:text-[var(--blue-dark)]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:hover:not(:disabled)]:[box-shadow:0_6px_16px_#14233824]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:focus-visible]:bg-[#eef2ff]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:focus-visible]:text-[var(--blue-dark)]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:focus-visible]:[box-shadow:0_6px_16px_#14233824]",
  "[[data-ui~=wizard-actions]_>_&]:w-full [[data-ui~=wizard-actions]_>_&]:text-[13px]",
  "mobile:[[data-ui~=wizard-actions]_>_&]:min-h-13.5 mobile:[[data-ui~=wizard-actions]_>_&]:rounded-2xl",
  "mobile:[[data-ui~=wizard-actions]_>_&]:text-[12px] [[data-ui~=loading-page]_>_&]:w-full",
  "[[data-ui~=result-sticky]_>_&]:flex-1 [[data-ui~=result-sticky]_>_&]:text-[12px]",
  "[[data-ui~=result-sticky]_>_&]:gap-[9px] mobile:[[data-ui~=result-sticky]_>_&]:text-[11px]",
  "mobile:[[data-ui~=result-sticky]_>_&]:min-h-[51px] mobile:[[data-ui~=result-sticky]_>_&]:py-[13px]",
  "mobile:[[data-ui~=result-sticky]_>_&]:px-[15px] mobile:[[data-ui~=result-sticky]_>_&]:gap-2",
  "mobile:[[data-ui~=result-sticky]_>_&]:rounded-[14px] narrow:[[data-ui~=result-sticky]_>_&]:text-[11px]",
  "mobile-type:[[data-ui~=result-sticky]_>_&]:text-[14px]",
  "[[data-ui~=result-sticky]_>_&_>_span:first-child]:flex-initial [[data-ui~=empty-state]_>_&]:w-full",
  "[[data-ui~=empty-state]_>_&]:max-w-75 [[data-ui~=empty-state]_>_&]:mb-[7px]",
  "[[data-ui~=empty-state]_>_&]:text-[12px] mobile:[[data-ui~=empty-state]_>_&]:text-[12px]",
  "[[data-ui~=preset-actions]_&]:w-full [[data-ui~=screen-loading]_[data-ui~=has-error]_>_&]:mb-2",
].join(" ");

export const selectedChoiceStyles = [
  "[[data-ui~=choice]&]:bg-[#f1f4ff] [[data-ui~=choice]&]:border-[#8a9bfa]",
  "[[data-ui~=duration-card]&]:bg-[#f2f5ff] [[data-ui~=duration-card]&]:border-[#8a9bfa]",
  "[[data-ui~=duration-card]&_>_span]:text-brand",
].join(" ");

export const softLavenderIconStyles = `${softIconStyles} [[data-ui~=soft-icon]&]:bg-[#f2edff] [[data-ui~=soft-icon]&]:text-[#8a64d6]`;

export const wizardFieldLabelStyles = `${fieldStyles} mobile:[&_select]:text-[16px] [[data-ui~=field-label]&]:mt-6`;

export const programDayHeadingStyles = `
  flex items-center gap-3 mb-5 [&_>_span]:size-8.5 [&_>_span]:shrink-0 [&_>_span]:grid
  [&_>_span]:place-items-center [&_>_span]:rounded-[11px] [&_>_span]:bg-[#eaf0ff]
  [&_>_span]:text-brand [&_>_span]:text-[12px] [&_>_span]:font-extrabold [&_h3]:text-[16px]
  [&_h3]:leading-[1.5]
`;

export const programTimelineStyles = `
  [list-style:none] py-0 pr-0 pl-3.5 m-0 [&_li]:relative [&_li]:[border-left:1px_solid_#dfe5f4]
  [&_li]:pt-0 [&_li]:pr-0 [&_li]:pb-6 [&_li]:pl-5.5 [&_li::before]:[content:'']
  [&_li::before]:absolute [&_li::before]:top-[5px] [&_li::before]:-left-1 [&_li::before]:size-[7px]
  [&_li::before]:bg-brand [&_li::before]:rounded-[50%] [&_li::before]:[box-shadow:0_0_0_4px_#f8f9fc]
  [&_li:last-child]:border-[transparent] [&_li:last-child]:pb-0 [&_time]:text-brand
  [&_time]:text-[11px] [&_time]:font-[750] [&_h4]:text-[16px] [&_h4]:my-2 [&_h4]:mx-0
  [&_h4]:leading-[1.4] [&_p]:text-[13px] [&_p]:leading-[1.8] [&_p]:text-[#687389]
  preset-mobile:[&_p]:text-[14px] [&_a]:inline-flex [&_a]:items-center [&_a]:gap-1.5 [&_a]:min-h-11
  [&_a]:py-2 [&_a]:px-0 [&_a]:text-[11px] [&_a]:leading-[1.5] [&_a]:no-underline
  preset-mobile:[&_a]:text-[12px]
`;
