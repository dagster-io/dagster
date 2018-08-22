// import * as React from "react";
// import gql from "graphql-tag";
// import styled from "styled-components";
// import { H5, H6, Text, UL, Code, Collapse } from "@blueprintjs/core";
// import SpacedCard from "./SpacedCard";
// import TypeWithTooltip from "./TypeWithTooltip";
// import Description from "./Description";
// import { SourceFragment } from "./types/SourceFragment";
// import { MaterializationFragment } from "./types/MaterializationFragment";
// import { PipelineContextFragment } from "./types/PipelineContextFragment";

// interface IArgumentedProps {
//   // XXX(freiksenet): Fix
//   item: SourceFragment & MaterializationFragment & PipelineContextFragment;
//   renderCard?: (props: any) => React.ReactNode;
// }

// export default class Argumented extends React.Component<IArgumentedProps, {}> {
//   static fragments = {
//     SourceFragment: gql`
//       fragment SourceFragment on Source {
//         name: sourceType
//         description
//         arguments {
//           name
//           description
//           type {
//             ...TypeFragment
//           }
//           isOptional
//         }
//       }

//       ${TypeWithTooltip.fragments.TypeFragment}
//     `,
//     MaterializationFragment: gql`
//       fragment MaterializationFragment on Materialization {
//         name
//         description
//         arguments {
//           name
//           description
//           type {
//             ...TypeFragment
//           }
//           isOptional
//         }
//       }

//       ${TypeWithTooltip.fragments.TypeFragment}
//     `,
//     PipelineContextFragment: gql`
//       fragment PipelineContextFragment on PipelineContext {
//         name
//         description
//         arguments {
//           name
//           description
//           type {
//             ...TypeFragment
//           }
//           isOptional
//         }
//       }

//       ${TypeWithTooltip.fragments.TypeFragment}
//     `
//   };

//   public render() {
//     const renderCard =
//       this.props.renderCard || ((props: any) => <SpacedCard {...props} />);
//     return renderCard({
//       elevation: 2,
//       children: (
//         <>
//           <H5>
//             <Code>{this.props.item.name}</Code>
//           </H5>
//           <DescriptionWrapper>
//             <Description description={this.props.item.description} />
//           </DescriptionWrapper>
//           <H6>Arguments</H6>
//           <UL>
//             {this.props.item.arguments.map((argument: any, i: number) => (
//               <li key={i}>
//                 {argument.name} {argument.isOptional ? "(optional)" : null}{" "}
//                 <TypeWithTooltip type={argument.type} />
//                 <DescriptionWrapper>
//                   <Description description={argument.description} />
//                 </DescriptionWrapper>
//               </li>
//             ))}
//           </UL>
//         </>
//       )
//     });
//   }
// }

// const DescriptionWrapper = styled.div`
//   max-width: 400px;
//   margin-bottom: 10px;
// `;
